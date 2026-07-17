from __future__ import annotations

import subprocess
import sys
import time
import webbrowser
import json
import threading
from pathlib import Path
from queue import Empty, Queue
from tkinter import BOTH, END, LEFT, RIGHT, X, StringVar, Tk, Toplevel, filedialog, messagebox, simpledialog
from tkinter import ttk
from urllib.parse import urlsplit

from .api_server import LocalApiServer
from .constants import APP_VERSION
from .control_signal import ControlSignals
from .database import Database
from .eagle import EagleClient, EagleImportError, EagleUnavailable
from .security import PairingManager
from .service import ProcessingService
from .updater import (
    UpdateError,
    UpdateInfo,
    automatic_check_due,
    check_for_update,
    launch_installer,
    prepare_update,
    record_successful_check,
)
from .url_utils import InvalidPageUrl, clean_page_url, normalize_domain


STATUS_TEXT = {
    "waiting_source": "等待处理",
    "queued": "等待处理",
    "waiting_eagle": "等待 Eagle",
    "retry": "等待自动重试",
    "imported": "导入成功",
    "skipped_duplicate": "重复跳过",
    "ignored_non_video": "非视频忽略",
    "ignored_by_user": "本次忽略",
    "failed_permanent": "导入失败",
}


def _set_window_icon(window: Tk | Toplevel) -> None:
    candidates: list[Path] = []
    bundle_root = getattr(sys, "_MEIPASS", "")
    if bundle_root:
        candidates.append(Path(bundle_root) / "assets" / "download-transfer-station.ico")
    candidates.append(
        Path(__file__).resolve().parents[2]
        / "assets"
        / "download-transfer-station.ico"
    )
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            window.iconbitmap(default=str(candidate))
            return
        except Exception:
            continue


class SiteRulesWindow:
    def __init__(self, parent: "MainWindow") -> None:
        self.parent = parent
        self.database = parent.database
        self.window = Toplevel(parent.root)
        self.window.title("自动导入网站")
        self.window.geometry("720x430")
        self.window.minsize(580, 340)
        self.window.transient(parent.root)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.summary_text = StringVar()
        self.refresh_after_id: str | None = None
        self._build()
        self.refresh()

    def _build(self) -> None:
        outer = ttk.Frame(self.window, padding=16)
        outer.pack(fill=BOTH, expand=True)

        ttk.Label(
            outer,
            text="自动导入网站",
            font=("Microsoft YaHei UI", 15, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            outer,
            text="只有列表中已开启的网站会自动保存来源；未列出的网站默认不导入。",
            foreground="#475569",
        ).pack(fill=X, pady=(6, 2))
        ttk.Label(outer, textvariable=self.summary_text).pack(fill=X, pady=(0, 10))

        columns = ("domain", "status", "subdomains", "updated")
        self.tree = ttk.Treeview(
            outer,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("domain", text="网站")
        self.tree.heading("status", text="自动导入")
        self.tree.heading("subdomains", text="子域名")
        self.tree.heading("updated", text="最近修改")
        self.tree.column("domain", width=280)
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("subdomains", width=120, anchor="center")
        self.tree.column("updated", width=150, anchor="center")
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<Double-1>", lambda _event: self.toggle_enabled())

        actions = ttk.Frame(outer, padding=(0, 10, 0, 0))
        actions.pack(fill=X)
        ttk.Button(actions, text="新增并开启", command=self.add_rule).pack(side=LEFT)
        ttk.Button(actions, text="开启 / 关闭", command=self.toggle_enabled).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="切换子域名", command=self.toggle_subdomains).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="删除规则", command=self.delete_rule).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="关闭", command=self.close).pack(side=RIGHT)

    def selected_rule(self) -> dict | None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个网站", parent=self.window)
            return None
        domain = self.tree.item(selected[0], "values")[0]
        return next(
            (rule for rule in self.database.list_site_rules() if rule["domain"] == domain),
            None,
        )

    def add_rule(self) -> None:
        value = simpledialog.askstring(
            "新增网站",
            "输入网站域名，例如：www.example.com",
            parent=self.window,
        )
        if not value:
            return
        try:
            domain = normalize_domain(value)
            self.database.set_site_rule(domain, True, True)
        except InvalidPageUrl as exc:
            messagebox.showerror("域名无效", str(exc), parent=self.window)
            return
        self.refresh(force=True, select_domain=domain)

    def toggle_enabled(self) -> None:
        rule = self.selected_rule()
        if not rule:
            return
        self.database.set_site_rule(
            rule["domain"],
            not bool(rule["enabled"]),
            bool(rule["include_subdomains"]),
        )
        self.refresh(force=True, select_domain=rule["domain"])

    def toggle_subdomains(self) -> None:
        rule = self.selected_rule()
        if not rule:
            return
        self.database.set_site_rule(
            rule["domain"],
            bool(rule["enabled"]),
            not bool(rule["include_subdomains"]),
        )
        self.refresh(force=True, select_domain=rule["domain"])

    def delete_rule(self) -> None:
        rule = self.selected_rule()
        if not rule:
            return
        if not messagebox.askyesno(
            "删除规则",
            f"删除 {rule['domain']} 后，该网站将按默认规则处理（不自动导入）。是否继续？",
            parent=self.window,
        ):
            return
        self.database.delete_site_rule(rule["domain"])
        self.refresh(force=True)

    def refresh(self, force: bool = False, select_domain: str | None = None) -> None:
        if not self.window.winfo_exists():
            return
        if self.refresh_after_id:
            self.window.after_cancel(self.refresh_after_id)
            self.refresh_after_id = None
        selected = select_domain
        if not selected and self.tree.selection():
            selected = str(self.tree.item(self.tree.selection()[0], "values")[0])

        rules = self.database.list_site_rules()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for rule in rules:
            updated = time.strftime(
                "%Y-%m-%d %H:%M",
                time.localtime(rule["updated_at"]),
            )
            self.tree.insert(
                "",
                END,
                iid=rule["domain"],
                values=(
                    rule["domain"],
                    "已开启" if rule["enabled"] else "已关闭",
                    "包含子域名" if rule["include_subdomains"] else "仅此域名",
                    updated,
                ),
            )
        if selected and self.tree.exists(selected):
            self.tree.selection_set(selected)
            self.tree.see(selected)
        enabled_count = sum(1 for rule in rules if rule["enabled"])
        disabled_count = len(rules) - enabled_count
        self.summary_text.set(
            f"已开启 {enabled_count} 个 · 已关闭 {disabled_count} 个 · 双击可快速切换"
        )
        self.parent.refresh(force=True)
        self.refresh_after_id = self.window.after(3000, self.refresh)

    def focus(self) -> None:
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

    def close(self) -> None:
        if self.refresh_after_id:
            self.window.after_cancel(self.refresh_after_id)
            self.refresh_after_id = None
        self.parent.site_rules_window = None
        self.window.destroy()


class MainWindow:
    def __init__(
        self,
        database: Database,
        api_server: LocalApiServer,
        processing: ProcessingService,
        external_tray: bool = False,
        start_hidden: bool = False,
    ) -> None:
        self.database = database
        self.api_server = api_server
        self.processing = processing
        self.external_tray = external_tray
        self.start_hidden = start_hidden and external_tray
        self.eagle = EagleClient()
        self.pairing = PairingManager(database)
        self.root = Tk()
        _set_window_icon(self.root)
        if self.start_hidden:
            self.root.withdraw()
        self.root.title("下载中转站")
        self.root.geometry("980x600")
        self.root.minsize(760, 440)
        self.root.protocol("WM_DELETE_WINDOW", self.hide if external_tray else self.quit)
        self.status_text = StringVar()
        self.pairing_text = StringVar()
        self.site_rules_text = StringVar(value="网站规则")
        self.update_button_text = StringVar(value="检查更新")
        self.control_signals = ControlSignals() if external_tray else None
        self.control_after_id: str | None = None
        self.refresh_after_id: str | None = None
        self.update_poll_after_id: str | None = None
        self.auto_update_after_id: str | None = None
        self.update_events: Queue[tuple[str, object]] = Queue()
        self.update_checking = False
        self.update_downloading = False
        self.visible = not self.start_hidden
        self.site_rules_window: SiteRulesWindow | None = None
        self.last_jobs_revision: tuple[int, float] | None = None
        self.last_eagle_check = 0.0
        self.eagle_connected = False
        self._build()
        self.refresh()
        if self.control_signals:
            self.control_after_id = self.root.after(250, self._poll_control_signals)
        self.auto_update_after_id = self.root.after(10000, self._automatic_update_check)

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill=BOTH, expand=True)

        heading = ttk.Frame(outer)
        heading.pack(fill=X)
        ttk.Label(
            heading,
            text="下载中转站",
            font=("Microsoft YaHei UI", 16, "bold"),
        ).pack(side=LEFT)
        ttk.Label(heading, textvariable=self.status_text).pack(side=RIGHT)

        ttk.Label(
            outer,
            text="直接导入模式：来源网页是可选信息，没有来源也会导入 Eagle。",
            foreground="#475569",
        ).pack(fill=X, pady=(8, 0))

        pairing = ttk.Frame(outer, padding=(0, 12, 0, 8))
        pairing.pack(fill=X)
        ttk.Label(pairing, textvariable=self.pairing_text).pack(side=LEFT)
        ttk.Button(pairing, text="复制配对码", command=self.copy_pairing_code).pack(
            side=LEFT, padx=(10, 0)
        )
        ttk.Button(pairing, text="解除 Chrome 配对", command=self.unpair).pack(
            side=LEFT, padx=(8, 0)
        )
        ttk.Button(pairing, textvariable=self.site_rules_text, command=self.show_site_rules).pack(
            side=LEFT, padx=(8, 0)
        )
        self.update_button = ttk.Button(
            pairing,
            textvariable=self.update_button_text,
            command=self.check_for_updates,
        )
        self.update_button.pack(side=RIGHT)

        columns = ("time", "status", "file", "source", "message")
        self.tree = ttk.Treeview(outer, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("time", text="时间")
        self.tree.heading("status", text="状态")
        self.tree.heading("file", text="文件")
        self.tree.heading("source", text="来源网站")
        self.tree.heading("message", text="说明")
        self.tree.column("time", width=130, anchor="center")
        self.tree.column("status", width=90, anchor="center")
        self.tree.column("file", width=240)
        self.tree.column("source", width=200)
        self.tree.column("message", width=250)
        self.tree.pack(fill=BOTH, expand=True)

        actions = ttk.Frame(outer, padding=(0, 10, 0, 0))
        actions.pack(fill=X)
        ttk.Button(actions, text="刷新", command=self.refresh).pack(side=LEFT)
        ttk.Button(actions, text="立即重试（可选）", command=self.retry_selected).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="打开文件位置", command=self.open_file_location).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="打开来源网页", command=self.open_source).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="补充/修改来源", command=self.assign_source).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="导出诊断", command=self.export_diagnostics).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="清理已完成", command=self.clear_history).pack(side=LEFT, padx=6)
        if self.external_tray:
            ttk.Button(actions, text="隐藏到右下角", command=self.hide).pack(side=RIGHT)
        else:
            ttk.Button(actions, text="最小化窗口", command=self.root.iconify).pack(side=RIGHT)

    def run(self) -> None:
        self.root.mainloop()

    def show(self) -> None:
        self.visible = True
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.refresh(force=True)

    def hide(self) -> None:
        self.visible = False
        self.root.withdraw()

    def _poll_control_signals(self) -> None:
        if not self.control_signals:
            return
        if self.control_signals.poll_quit():
            self.quit()
            return
        if self.control_signals.poll_show():
            self.show()
        if self.control_signals.poll_rules():
            self.show()
            self.show_site_rules()
        if self.control_signals.poll_update():
            self.show()
            self.check_for_updates()
        self.control_after_id = self.root.after(250, self._poll_control_signals)

    def _automatic_update_check(self) -> None:
        self.auto_update_after_id = None
        if automatic_check_due():
            self.check_for_updates(silent=True)

    def check_for_updates(self, silent: bool = False) -> None:
        if self.update_checking or self.update_downloading:
            if not silent:
                messagebox.showinfo("正在更新", "更新检查或下载正在进行，请稍候。")
            return
        self.update_checking = True
        self.update_button.configure(state="disabled")
        self.update_button_text.set("正在检查…")
        threading.Thread(
            target=self._check_update_worker,
            args=(silent,),
            daemon=True,
        ).start()
        self._ensure_update_poll()

    def _check_update_worker(self, silent: bool) -> None:
        try:
            update = check_for_update()
            record_successful_check()
            self.update_events.put(("check_ok", (silent, update)))
        except Exception as exc:
            self.update_events.put(("check_error", (silent, exc)))

    def _ensure_update_poll(self) -> None:
        if self.update_poll_after_id is None:
            self.update_poll_after_id = self.root.after(150, self._poll_update_events)

    def _poll_update_events(self) -> None:
        self.update_poll_after_id = None
        while True:
            try:
                event, payload = self.update_events.get_nowait()
            except Empty:
                break
            if event == "check_ok":
                silent, update = payload
                self._handle_update_check(bool(silent), update)
            elif event == "check_error":
                silent, error = payload
                self._handle_update_error(bool(silent), error)
            elif event == "download_progress":
                downloaded, total = payload
                percent = min(99, int(int(downloaded) * 100 / max(1, int(total))))
                self.update_button_text.set(f"正在下载 {percent}%")
            elif event == "download_ok":
                self._handle_download_ready(payload)
            elif event == "download_error":
                self._handle_download_error(payload)
        if self.update_checking or self.update_downloading:
            self._ensure_update_poll()

    def _reset_update_button(self) -> None:
        self.update_button_text.set("检查更新")
        self.update_button.configure(state="normal")

    def _handle_update_check(self, silent: bool, update: object) -> None:
        self.update_checking = False
        self._reset_update_button()
        if update is None:
            if not silent:
                messagebox.showinfo("已经是最新版", f"当前版本 v{APP_VERSION} 已是最新版。")
            return
        if not isinstance(update, UpdateInfo):
            self._handle_update_error(silent, UpdateError("更新信息无效"))
            return
        if not self.visible:
            self.show()
        details = f"发现新版本 v{update.version}，是否现在一键更新？"
        if update.notes:
            details += "\n\n" + update.notes[:1200]
        if not messagebox.askyesno("发现新版本", details, parent=self.root):
            return
        self._start_update_download(update)

    def _handle_update_error(self, silent: bool, error: object) -> None:
        self.update_checking = False
        self._reset_update_button()
        if not silent:
            messagebox.showwarning("检查更新失败", str(error), parent=self.root)

    def _start_update_download(self, update: UpdateInfo) -> None:
        self.update_downloading = True
        self.update_button.configure(state="disabled")
        self.update_button_text.set("正在下载 0%")
        threading.Thread(
            target=self._download_update_worker,
            args=(update,),
            daemon=True,
        ).start()
        self._ensure_update_poll()

    def _download_update_worker(self, update: UpdateInfo) -> None:
        try:
            installer = prepare_update(
                update,
                lambda current, total: self.update_events.put(
                    ("download_progress", (current, total))
                ),
            )
            self.update_events.put(("download_ok", installer))
        except Exception as exc:
            self.update_events.put(("download_error", exc))

    def _handle_download_ready(self, installer: object) -> None:
        self.update_downloading = False
        self.update_button_text.set("正在安装…")
        try:
            launch_installer(Path(installer))
        except Exception as exc:
            self._handle_download_error(exc)
            return
        self.root.after(350, self.quit)

    def _handle_download_error(self, error: object) -> None:
        self.update_downloading = False
        self._reset_update_button()
        messagebox.showerror("更新失败", str(error), parent=self.root)

    def refresh(self, force: bool = False) -> None:
        if self.refresh_after_id:
            self.root.after_cancel(self.refresh_after_id)
            self.refresh_after_id = None
        if not self.visible and not force:
            self.refresh_after_id = self.root.after(30000, self.refresh)
            return

        now = time.time()
        if force or now - self.last_eagle_check >= 10:
            self.eagle_connected = self.eagle.is_available()
            self.last_eagle_check = now
        eagle_text = "Eagle 已连接" if self.eagle_connected else "正在等待 Eagle"
        host, port = self.api_server.address
        counts = self.database.job_status_counts()
        active_count = sum(
            counts.get(status, 0)
            for status in ("waiting_source", "queued", "waiting_eagle", "retry")
        )
        status_parts = [f"v{APP_VERSION}", eagle_text, f"本机服务 {host}:{port}"]
        if active_count:
            status_parts.append(f"处理中 {active_count}")
        if counts.get("failed_permanent", 0):
            status_parts.append(f"失败 {counts['failed_permanent']}")
        self.status_text.set(" · ".join(status_parts))
        enabled_sites = sum(
            1 for rule in self.database.list_site_rules() if rule["enabled"]
        )
        self.site_rules_text.set(f"网站规则（已开启 {enabled_sites}）")
        if self.pairing.paired_origin:
            self.pairing_text.set("Chrome 已安全配对")
        else:
            self.pairing_text.set(f"Chrome 配对码：{self.pairing.pairing_code}")

        revision = self.database.jobs_revision()
        if force or revision != self.last_jobs_revision:
            selected = self.selected_job_id()
            for item in self.tree.get_children():
                self.tree.delete(item)
            for job in self.database.list_jobs(500):
                created = time.strftime("%Y-%m-%d %H:%M", time.localtime(job["created_at"]))
                source = "未记录"
                if job.get("source_url"):
                    source = urlsplit(job["source_url"]).hostname or "已记录"
                message = job.get("error_message") or ""
                if job["status"] == "imported" and not job.get("source_url"):
                    message = "已直接导入，未保存来源网页"
                self.tree.insert(
                    "",
                    END,
                    iid=job["id"],
                    values=(
                        created,
                        STATUS_TEXT.get(job["status"], job["status"]),
                        job["file_name"],
                        source,
                        message,
                    ),
                )
            if selected and self.tree.exists(selected):
                self.tree.selection_set(selected)
            self.last_jobs_revision = revision
        self.refresh_after_id = self.root.after(5000, self.refresh)

    def selected_job_id(self) -> str | None:
        selected = self.tree.selection()
        return selected[0] if selected else None

    def selected_job(self) -> dict | None:
        job_id = self.selected_job_id()
        return self.database.get_job(job_id) if job_id else None

    def retry_selected(self) -> None:
        job_id = self.selected_job_id()
        if not job_id:
            messagebox.showinfo("提示", "请先选择一条记录")
            return
        if not self.database.retry_job(job_id):
            self.refresh(force=True)
            messagebox.showinfo("无需重试", "这条记录已经处理完成，不需要再次重试。")
            return
        self.processing.wake()
        self.refresh()

    def open_file_location(self) -> None:
        job = self.selected_job()
        if not job:
            messagebox.showinfo("提示", "请先选择一条记录")
            return
        path = Path(job["file_path"])
        if not path.exists():
            messagebox.showwarning("文件不存在", "下载文件已经不在原位置")
            return
        subprocess.Popen(["explorer.exe", "/select,", str(path)])

    def open_source(self) -> None:
        job = self.selected_job()
        if not job or not job.get("source_url"):
            messagebox.showinfo("没有来源", "这条记录还没有匹配到来源网页")
            return
        webbrowser.open(job["source_url"])

    def assign_source(self) -> None:
        job = self.selected_job()
        if not job:
            messagebox.showinfo("提示", "请先选择一条记录")
            return
        value = simpledialog.askstring(
            "补充来源网页",
            "请输入视频所在网页地址：",
            parent=self.root,
        )
        if not value:
            return
        try:
            cleaned = clean_page_url(value)
        except ValueError as exc:
            messagebox.showerror("网址无效", str(exc))
            return

        if job["status"] == "imported":
            if not job.get("eagle_item_id"):
                messagebox.showwarning("无法更新", "这条旧记录没有 Eagle 项目编号，无法自动补写来源。")
                return
            try:
                self.eagle.update_source(str(job["eagle_item_id"]), cleaned)
            except (EagleUnavailable, EagleImportError) as exc:
                messagebox.showerror("更新失败", str(exc))
                return
            self.database.record_imported_source(job["id"], cleaned)
            self.refresh(force=True)
            messagebox.showinfo("更新完成", "来源网址已经写入现有 Eagle 项目，不会重复导入文件。")
            return

        if job["status"] == "skipped_duplicate":
            messagebox.showinfo("重复项目", "这条记录因内容重复被跳过，没有新的 Eagle 项目可以补写来源。")
            return

        self.database.assign_source(job["id"], cleaned)
        self.processing.wake()
        self.refresh(force=True)

    def export_diagnostics(self) -> None:
        target = filedialog.asksaveasfilename(
            parent=self.root,
            title="导出诊断记录",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json")],
            initialfile="idm-eagle-diagnostics.json",
        )
        if not target:
            return
        rows = []
        for job in self.database.list_jobs(500):
            source_domain = ""
            if job.get("source_url"):
                source_domain = urlsplit(job["source_url"]).hostname or ""
            rows.append(
                {
                    "time": job["created_at"],
                    "status": job["status"],
                    "fileName": job["file_name"],
                    "sourceDomain": source_domain,
                    "attempts": job["attempt_count"],
                    "errorCode": job.get("error_code"),
                    "errorMessage": job.get("error_message"),
                }
            )
        Path(target).write_text(
            json.dumps(
                {"formatVersion": 1, "appVersion": APP_VERSION, "jobs": rows},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        messagebox.showinfo("导出完成", "诊断记录已保存。完整路径和来源网址未包含在文件中。")

    def clear_history(self) -> None:
        if not messagebox.askyesno(
            "清理记录",
            "只清理成功、失败和已跳过记录；等待中的任务不会删除。是否继续？",
        ):
            return
        count = self.database.clear_terminal_history()
        self.refresh(force=True)
        messagebox.showinfo("清理完成", f"已清理 {count} 条历史记录。")

    def copy_pairing_code(self) -> None:
        code = self.pairing.pairing_code
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        self.root.update()

    def show_site_rules(self) -> None:
        if self.site_rules_window and self.site_rules_window.window.winfo_exists():
            self.site_rules_window.focus()
            return
        self.site_rules_window = SiteRulesWindow(self)

    def unpair(self) -> None:
        if not self.pairing.paired_origin:
            messagebox.showinfo("未配对", "当前没有已配对的 Chrome 扩展")
            return
        if not messagebox.askyesno("解除配对", "解除后需要重新输入配对码，是否继续？"):
            return
        self.pairing.unpair()
        self.refresh(force=True)

    def quit(self) -> None:
        if self.site_rules_window and self.site_rules_window.window.winfo_exists():
            self.site_rules_window.close()
        if self.refresh_after_id:
            self.root.after_cancel(self.refresh_after_id)
            self.refresh_after_id = None
        if self.control_after_id:
            self.root.after_cancel(self.control_after_id)
            self.control_after_id = None
        if self.update_poll_after_id:
            self.root.after_cancel(self.update_poll_after_id)
            self.update_poll_after_id = None
        if self.auto_update_after_id:
            self.root.after_cancel(self.auto_update_after_id)
            self.auto_update_after_id = None
        if self.control_signals:
            self.control_signals.close()
            self.control_signals = None
        self.root.quit()
        self.root.destroy()
