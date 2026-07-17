using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("下载中转站安装程序")]
[assembly: AssemblyDescription("下载中转站一键安装程序")]
[assembly: AssemblyProduct("下载中转站")]
[assembly: AssemblyCompany("下载中转站")]
[assembly: AssemblyVersion("0.5.0.0")]
[assembly: AssemblyFileVersion("0.5.0.0")]

internal static class SetupProgram
{
    internal const string Version = "0.5.0";
    internal const string ProductName = "下载中转站";
    internal const string QuitEventName = @"Local\IdmEagleAutoImportQuit";
    internal const string DefaultIdmRegistry = @"Software\DownloadManager";
    internal const string DefaultStateRegistry = @"Software\IDMEagleAutoImport";
    internal const string DefaultUninstallRegistry = @"Software\Microsoft\Windows\CurrentVersion\Uninstall\IDMEagleAutoImport";

    [STAThread]
    private static int Main(string[] args)
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);

        if (args.Any(value => value == "--test-install"))
        {
            return RunTestInstall();
        }
        if (args.Any(value => value == "--test-uninstall"))
        {
            return RunTestUninstall();
        }
        int workerIndex = Array.IndexOf(args, "--uninstall-worker");
        if (workerIndex >= 0 && workerIndex + 1 < args.Length)
        {
            return RunUninstallWorker(args[workerIndex + 1]);
        }

        string executableName = Path.GetFileNameWithoutExtension(Application.ExecutablePath);
        bool uninstall = args.Any(value => value == "--uninstall")
            || executableName.IndexOf("卸载", StringComparison.OrdinalIgnoreCase) >= 0
            || executableName.IndexOf("uninstall", StringComparison.OrdinalIgnoreCase) >= 0;
        if (uninstall)
        {
            return BeginUninstall();
        }

        Application.Run(new InstallerForm());
        return 0;
    }

    private static int RunTestInstall()
    {
        try
        {
            InstallResult result = InstallerEngine.Install(true, delegate { });
            File.WriteAllText(
                Path.Combine(result.InstallDirectory, "install-test-result.txt"),
                result.IdmConfigured ? "OK" : "WARNING: " + result.Warning,
                new UTF8Encoding(false)
            );
            return 0;
        }
        catch (Exception exception)
        {
            string resultPath = Environment.GetEnvironmentVariable("IDM_EAGLE_TEST_RESULT") ?? "";
            if (!string.IsNullOrWhiteSpace(resultPath))
            {
                File.WriteAllText(resultPath, exception.ToString(), new UTF8Encoding(false));
            }
            return 1;
        }
    }

    private static int RunTestUninstall()
    {
        try
        {
            InstallerEngine.Uninstall(InstallerEngine.GetInstallDirectory(true), true);
            return 0;
        }
        catch (Exception exception)
        {
            string resultPath = Environment.GetEnvironmentVariable("IDM_EAGLE_TEST_RESULT") ?? "";
            if (!string.IsNullOrWhiteSpace(resultPath))
            {
                File.WriteAllText(resultPath, exception.ToString(), new UTF8Encoding(false));
            }
            return 1;
        }
    }

    private static int BeginUninstall()
    {
        if (MessageBox.Show(
            "将移除助手并恢复安装前的 IDM 设置。下载的视频和 Eagle 中已有项目不会删除。是否继续？",
            "卸载下载中转站",
            MessageBoxButtons.YesNo,
            MessageBoxIcon.Question
        ) != DialogResult.Yes)
        {
            return 0;
        }

        string installDirectory = InstallerEngine.GetInstallDirectory(false);
        string temporary = Path.Combine(
            Path.GetTempPath(),
            "IDMEagleUninstall-" + Guid.NewGuid().ToString("N") + ".exe"
        );
        File.Copy(Application.ExecutablePath, temporary, true);
        Process.Start(new ProcessStartInfo
        {
            FileName = temporary,
            Arguments = "--uninstall-worker " + QuoteArgument(installDirectory),
            UseShellExecute = false,
            CreateNoWindow = true,
            WindowStyle = ProcessWindowStyle.Hidden
        });
        return 0;
    }

    private static int RunUninstallWorker(string installDirectory)
    {
        try
        {
            InstallerEngine.Uninstall(installDirectory);
            MessageBox.Show(
                "卸载完成。历史记录和网站规则已保留，重新安装后可以继续使用。",
                "下载中转站",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            );
            MoveFileEx(Application.ExecutablePath, null, 0x4);
            return 0;
        }
        catch (Exception exception)
        {
            MessageBox.Show(
                "卸载未完成：" + exception.Message,
                "下载中转站",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            );
            return 1;
        }
    }

    internal static string QuoteArgument(string value)
    {
        return "\"" + value.Replace("\"", "\\\"") + "\"";
    }

    [System.Runtime.InteropServices.DllImport("kernel32.dll", CharSet = System.Runtime.InteropServices.CharSet.Unicode)]
    private static extern bool MoveFileEx(string existing, string replacement, int flags);
}

internal sealed class InstallerForm : Form
{
    private readonly Label status;
    private readonly Button installButton;
    private readonly Button closeButton;
    private readonly TextBox instructions;

    internal InstallerForm()
    {
        Text = SetupProgram.ProductName + " 一键安装";
        ClientSize = new Size(620, 410);
        MinimumSize = new Size(620, 410);
        MaximizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
        Font = new Font("Microsoft YaHei UI", 9F);
        Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);

        Label heading = new Label
        {
            Text = "下载中转站",
            Font = new Font("Microsoft YaHei UI", 18F, FontStyle.Bold),
            AutoSize = true,
            Location = new Point(28, 24)
        };
        Controls.Add(heading);

        Label description = new Label
        {
            Text = "自带运行环境，自动配置 IDM、创建快捷方式并启动助手。不会移动或删除下载文件。",
            AutoSize = false,
            Size = new Size(560, 44),
            Location = new Point(31, 72),
            ForeColor = Color.FromArgb(71, 85, 105)
        };
        Controls.Add(description);

        installButton = new Button
        {
            Text = "一键安装",
            Font = new Font("Microsoft YaHei UI", 13F, FontStyle.Bold),
            Size = new Size(180, 48),
            Location = new Point(31, 122)
        };
        installButton.Click += InstallClicked;
        Controls.Add(installButton);

        closeButton = new Button
        {
            Text = "关闭",
            Size = new Size(90, 32),
            Location = new Point(500, 350),
            Enabled = true
        };
        closeButton.Click += delegate { Close(); };
        Controls.Add(closeButton);

        status = new Label
        {
            Text = "准备就绪",
            AutoSize = false,
            Size = new Size(350, 46),
            Location = new Point(230, 126),
            TextAlign = ContentAlignment.MiddleLeft
        };
        Controls.Add(status);

        instructions = new TextBox
        {
            Multiline = true,
            ReadOnly = true,
            BorderStyle = BorderStyle.FixedSingle,
            Size = new Size(560, 145),
            Location = new Point(31, 190),
            BackColor = Color.White,
            Text = "安装完成后，Chrome 只需最后一步：\r\n\r\n1. 打开“开发者模式”\r\n2. 点击“加载已解压的扩展程序”\r\n3. 选择安装器自动打开的 chrome-extension 文件夹\r\n\r\n扩展加载后会自动安全配对，不需要输入配对码。"
        };
        Controls.Add(instructions);
    }

    private async void InstallClicked(object sender, EventArgs eventArgs)
    {
        installButton.Enabled = false;
        closeButton.Enabled = false;
        status.ForeColor = Color.Black;
        status.Text = "正在安装…";
        try
        {
            InstallResult result = await Task.Run(() => InstallerEngine.Install(false, Report));
            try
            {
                Clipboard.SetText(result.ExtensionDirectory);
            }
            catch
            {
            }
            status.ForeColor = result.IdmConfigured ? Color.DarkGreen : Color.DarkOrange;
            status.Text = result.IdmConfigured
                ? "安装完成，IDM 已自动配置"
                : "安装完成，但 IDM 需要手动确认";
            if (!string.IsNullOrWhiteSpace(result.Warning))
            {
                instructions.Text = result.Warning + "\r\n\r\n" + instructions.Text;
            }
            else
            {
                instructions.Text += "\r\n扩展目录已经复制到剪贴板。";
            }
            installButton.Text = "安装完成";
        }
        catch (Exception exception)
        {
            status.ForeColor = Color.DarkRed;
            status.Text = "安装失败";
            instructions.Text = exception.Message + "\r\n\r\n请保留完整安装包后重试。";
            installButton.Text = "重新安装";
            installButton.Enabled = true;
        }
        finally
        {
            closeButton.Enabled = true;
        }
    }

    private void Report(string message)
    {
        if (IsDisposed) return;
        BeginInvoke((Action)delegate { status.Text = message; });
    }
}

internal sealed class InstallResult
{
    internal string InstallDirectory = "";
    internal string ExtensionDirectory = "";
    internal bool IdmConfigured;
    internal string Warning = "";
}

internal static class InstallerEngine
{
    internal static string GetInstallDirectory(bool testMode)
    {
        if (testMode)
        {
            string overridePath = Environment.GetEnvironmentVariable("IDM_EAGLE_INSTALL_ROOT") ?? "";
            if (string.IsNullOrWhiteSpace(overridePath))
            {
                throw new InvalidOperationException("测试安装目录未设置");
            }
            return Path.GetFullPath(overridePath);
        }
        return Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "IDM-Eagle自动导入助手"
        );
    }

    internal static InstallResult Install(bool testMode, Action<string> report)
    {
        string payload = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "app");
        if (!File.Exists(Path.Combine(payload, "下载中转站.exe"))
            || !File.Exists(Path.Combine(payload, "runtime", "下载中转站后台", "下载中转站后台.exe")))
        {
            throw new InvalidOperationException("安装包不完整，请重新解压完整 ZIP 后再运行。");
        }

        string installDirectory = GetInstallDirectory(testMode);
        report("正在停止旧版本…");
        SignalQuit();
        Thread.Sleep(testMode ? 50 : 1000);

        report("正在复制程序文件…");
        Directory.CreateDirectory(installDirectory);
        CopyDirectory(payload, installDirectory);

        report("正在准备 Chrome 自动配对…");
        string extensionDirectory = Path.Combine(installDirectory, "chrome-extension");
        WriteBootstrapPairing(extensionDirectory, testMode);

        report("正在配置 IDM…");
        string warning;
        bool configured = ConfigureIdm(installDirectory, testMode, out warning);

        if (!testMode)
        {
            report("正在创建快捷方式…");
            InstallUninstaller(installDirectory);
            CreateShortcuts(installDirectory);
            RegisterUninstaller(installDirectory);

            report("正在启动助手…");
            Process.Start(new ProcessStartInfo
            {
                FileName = Path.Combine(installDirectory, "下载中转站.exe"),
                WorkingDirectory = installDirectory,
                UseShellExecute = true
            });
            OpenChromeSetup(extensionDirectory);
        }

        return new InstallResult
        {
            InstallDirectory = installDirectory,
            ExtensionDirectory = extensionDirectory,
            IdmConfigured = configured,
            Warning = warning
        };
    }

    private static void SignalQuit()
    {
        try
        {
            using (EventWaitHandle handle = EventWaitHandle.OpenExisting(SetupProgram.QuitEventName))
            {
                handle.Set();
            }
        }
        catch (WaitHandleCannotBeOpenedException)
        {
        }
        catch (UnauthorizedAccessException)
        {
        }
    }

    private static void CopyDirectory(string source, string destination)
    {
        foreach (string directory in Directory.GetDirectories(source, "*", SearchOption.AllDirectories))
        {
            string relative = directory.Substring(source.Length).TrimStart(Path.DirectorySeparatorChar);
            Directory.CreateDirectory(Path.Combine(destination, relative));
        }
        foreach (string file in Directory.GetFiles(source, "*", SearchOption.AllDirectories))
        {
            string relative = file.Substring(source.Length).TrimStart(Path.DirectorySeparatorChar);
            string target = Path.Combine(destination, relative);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            Exception lastError = null;
            for (int attempt = 0; attempt < 10; attempt++)
            {
                try
                {
                    File.Copy(file, target, true);
                    lastError = null;
                    break;
                }
                catch (IOException exception)
                {
                    lastError = exception;
                    Thread.Sleep(200);
                }
            }
            if (lastError != null) throw lastError;
        }
    }

    private static bool ConfigureIdm(
        string installDirectory,
        bool testMode,
        out string warning
    )
    {
        warning = "";
        string idmSubkey = testMode
            ? (Environment.GetEnvironmentVariable("IDM_EAGLE_IDM_REGISTRY_SUBKEY") ?? @"Software\IDMEagleAutoImport\InstallerTest\IDM")
            : SetupProgram.DefaultIdmRegistry;
        string stateSubkey = testMode
            ? (Environment.GetEnvironmentVariable("IDM_EAGLE_STATE_REGISTRY_SUBKEY") ?? @"Software\IDMEagleAutoImport\InstallerTest\State")
            : SetupProgram.DefaultStateRegistry;
        string hook = Path.Combine(installDirectory, "IdmEagleHook.exe");

        using (RegistryKey idm = Registry.CurrentUser.CreateSubKey(idmSubkey))
        using (RegistryKey state = Registry.CurrentUser.CreateSubKey(stateSubkey))
        {
            string currentProgram = Convert.ToString(idm.GetValue("VScannerProgram", ""));
            string currentParameters = Convert.ToString(idm.GetValue("VScannerParameters", ""));
            bool ours = string.Equals(
                Path.GetFileName(currentProgram),
                "IdmEagleHook.exe",
                StringComparison.OrdinalIgnoreCase
            );
            if (!string.IsNullOrWhiteSpace(currentProgram) && !ours)
            {
                warning = "检测到 IDM 已配置其他病毒扫描程序，为避免覆盖安全软件，本安装器没有修改该项。请在 IDM > 选项 > 下载 > 病毒检查选项中手动确认。";
                return false;
            }

            if (Convert.ToInt32(state.GetValue("BackupSaved", 0)) != 1)
            {
                bool assumeOriginallyEmpty = ours;
                state.SetValue("HadProgram", assumeOriginallyEmpty ? 0 : (string.IsNullOrEmpty(currentProgram) ? 0 : 1), RegistryValueKind.DWord);
                state.SetValue("PreviousProgram", assumeOriginallyEmpty ? "" : currentProgram, RegistryValueKind.String);
                state.SetValue("HadParameters", assumeOriginallyEmpty ? 0 : (string.IsNullOrEmpty(currentParameters) ? 0 : 1), RegistryValueKind.DWord);
                state.SetValue("PreviousParameters", assumeOriginallyEmpty ? "" : currentParameters, RegistryValueKind.String);
                state.SetValue("BackupSaved", 1, RegistryValueKind.DWord);
            }
            state.SetValue("InstallDirectory", installDirectory, RegistryValueKind.String);
            idm.SetValue("VScannerProgram", hook, RegistryValueKind.String);
            idm.SetValue("VScannerParameters", "[File]", RegistryValueKind.String);
        }
        return true;
    }

    private static void WriteBootstrapPairing(string extensionDirectory, bool testMode)
    {
        byte[] secretBytes = new byte[32];
        using (RandomNumberGenerator random = RandomNumberGenerator.Create())
        {
            random.GetBytes(secretBytes);
        }
        string secret = ToHex(secretBytes);
        File.WriteAllText(
            Path.Combine(extensionDirectory, "bootstrap.js"),
            "globalThis.IDM_EAGLE_BOOTSTRAP_SECRET = \"" + secret + "\";\r\n",
            new UTF8Encoding(false)
        );

        string dataDirectory = testMode
            ? Path.Combine(GetInstallDirectory(true), "test-data")
            : Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "IdmEagleAutoImport"
            );
        Directory.CreateDirectory(dataDirectory);
        byte[] hash;
        using (SHA256 sha = SHA256.Create())
        {
            hash = sha.ComputeHash(Encoding.UTF8.GetBytes(secret));
        }
        long expiresAt = (long)(DateTime.UtcNow.AddDays(7) - new DateTime(1970, 1, 1)).TotalSeconds;
        string json = "{\"secretHash\":\"" + ToHex(hash) + "\",\"expiresAt\":" + expiresAt + "}";
        File.WriteAllText(
            Path.Combine(dataDirectory, "pairing-bootstrap.json"),
            json,
            new UTF8Encoding(false)
        );
    }

    private static string ToHex(byte[] bytes)
    {
        StringBuilder builder = new StringBuilder(bytes.Length * 2);
        foreach (byte value in bytes) builder.Append(value.ToString("x2"));
        return builder.ToString();
    }

    private static void InstallUninstaller(string installDirectory)
    {
        string target = Path.Combine(installDirectory, "卸载助手.exe");
        File.Copy(Application.ExecutablePath, target, true);
    }

    private static void CreateShortcuts(string installDirectory)
    {
        DeleteLegacyShortcuts();
        string target = Path.Combine(installDirectory, "下载中转站.exe");
        string desktop = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
            "下载中转站.lnk"
        );
        string startFolder = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.StartMenu),
            "Programs",
            "下载中转站"
        );
        Directory.CreateDirectory(startFolder);
        CreateShortcut(desktop, target, "", installDirectory);
        CreateShortcut(Path.Combine(startFolder, "打开助手.lnk"), target, "", installDirectory);
        CreateShortcut(
            Path.Combine(startFolder, "卸载助手.lnk"),
            Path.Combine(installDirectory, "卸载助手.exe"),
            "--uninstall",
            installDirectory
        );
    }

    private static void DeleteLegacyShortcuts()
    {
        string legacyDesktop = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
            "IDM → Eagle 自动导入助手.lnk"
        );
        if (File.Exists(legacyDesktop)) File.Delete(legacyDesktop);
        string legacyStartFolder = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.StartMenu),
            "Programs",
            "IDM → Eagle 自动导入助手"
        );
        if (Directory.Exists(legacyStartFolder)) Directory.Delete(legacyStartFolder, true);
    }

    private static void CreateShortcut(string path, string target, string arguments, string workingDirectory)
    {
        Type shellType = Type.GetTypeFromProgID("WScript.Shell");
        dynamic shell = Activator.CreateInstance(shellType);
        dynamic shortcut = shell.CreateShortcut(path);
        shortcut.TargetPath = target;
        shortcut.Arguments = arguments;
        shortcut.WorkingDirectory = workingDirectory;
        shortcut.IconLocation = target + ",0";
        shortcut.Save();
    }

    private static void RegisterUninstaller(string installDirectory)
    {
        using (RegistryKey key = Registry.CurrentUser.CreateSubKey(SetupProgram.DefaultUninstallRegistry))
        {
            key.SetValue("DisplayName", SetupProgram.ProductName, RegistryValueKind.String);
            key.SetValue("DisplayVersion", SetupProgram.Version, RegistryValueKind.String);
            key.SetValue("Publisher", "下载中转站", RegistryValueKind.String);
            key.SetValue("InstallLocation", installDirectory, RegistryValueKind.String);
            key.SetValue(
                "UninstallString",
                SetupProgram.QuoteArgument(Path.Combine(installDirectory, "卸载助手.exe")) + " --uninstall",
                RegistryValueKind.String
            );
            key.SetValue("NoModify", 1, RegistryValueKind.DWord);
            key.SetValue("NoRepair", 0, RegistryValueKind.DWord);
        }
    }

    private static void OpenChromeSetup(string extensionDirectory)
    {
        try
        {
            Process.Start("explorer.exe", SetupProgram.QuoteArgument(extensionDirectory));
        }
        catch
        {
        }
        string chrome = FindChrome();
        try
        {
            if (!string.IsNullOrEmpty(chrome))
            {
                Process.Start(chrome, "chrome://extensions/");
            }
        }
        catch
        {
        }
    }

    private static string FindChrome()
    {
        string[] candidates = new[]
        {
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Google", "Chrome", "Application", "chrome.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Google", "Chrome", "Application", "chrome.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Google", "Chrome", "Application", "chrome.exe")
        };
        return candidates.FirstOrDefault(File.Exists) ?? "";
    }

    internal static void Uninstall(string installDirectory, bool testMode = false)
    {
        string fullInstall = Path.GetFullPath(installDirectory).TrimEnd(Path.DirectorySeparatorChar);
        string expected = (testMode
            ? GetInstallDirectory(true)
            : Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "IDM-Eagle自动导入助手"
            )).TrimEnd(Path.DirectorySeparatorChar);
        if (!string.Equals(fullInstall, expected, StringComparison.OrdinalIgnoreCase)
            || !File.Exists(Path.Combine(fullInstall, "下载中转站.exe")))
        {
            throw new InvalidOperationException("安装目录校验失败，未删除任何文件。");
        }

        SignalQuit();
        Thread.Sleep(testMode ? 50 : 1200);
        RestoreIdm(fullInstall, testMode);
        if (!testMode)
        {
            DeleteShortcuts();
            Registry.CurrentUser.DeleteSubKeyTree(SetupProgram.DefaultUninstallRegistry, false);
        }

        Exception lastError = null;
        for (int attempt = 0; attempt < 15; attempt++)
        {
            try
            {
                Directory.Delete(fullInstall, true);
                lastError = null;
                break;
            }
            catch (IOException exception)
            {
                lastError = exception;
                Thread.Sleep(300);
            }
            catch (UnauthorizedAccessException exception)
            {
                lastError = exception;
                Thread.Sleep(300);
            }
        }
        if (lastError != null) throw lastError;
    }

    private static void RestoreIdm(string installDirectory, bool testMode)
    {
        string idmSubkey = testMode
            ? (Environment.GetEnvironmentVariable("IDM_EAGLE_IDM_REGISTRY_SUBKEY") ?? @"Software\IDMEagleAutoImport\InstallerTest\IDM")
            : SetupProgram.DefaultIdmRegistry;
        string stateSubkey = testMode
            ? (Environment.GetEnvironmentVariable("IDM_EAGLE_STATE_REGISTRY_SUBKEY") ?? @"Software\IDMEagleAutoImport\InstallerTest\State")
            : SetupProgram.DefaultStateRegistry;
        using (RegistryKey state = Registry.CurrentUser.OpenSubKey(stateSubkey, false))
        using (RegistryKey idm = Registry.CurrentUser.CreateSubKey(idmSubkey))
        {
            if (state == null) return;
            string current = Convert.ToString(idm.GetValue("VScannerProgram", ""));
            string installedHook = Path.Combine(installDirectory, "IdmEagleHook.exe");
            if (!string.Equals(current, installedHook, StringComparison.OrdinalIgnoreCase)) return;

            if (Convert.ToInt32(state.GetValue("HadProgram", 0)) == 1)
                idm.SetValue("VScannerProgram", Convert.ToString(state.GetValue("PreviousProgram", "")), RegistryValueKind.String);
            else
                idm.DeleteValue("VScannerProgram", false);

            if (Convert.ToInt32(state.GetValue("HadParameters", 0)) == 1)
                idm.SetValue("VScannerParameters", Convert.ToString(state.GetValue("PreviousParameters", "")), RegistryValueKind.String);
            else
                idm.DeleteValue("VScannerParameters", false);
        }
        Registry.CurrentUser.DeleteSubKeyTree(stateSubkey, false);
    }

    private static void DeleteShortcuts()
    {
        DeleteLegacyShortcuts();
        string desktop = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
            "下载中转站.lnk"
        );
        if (File.Exists(desktop)) File.Delete(desktop);
        string startFolder = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.StartMenu),
            "Programs",
            "下载中转站"
        );
        if (Directory.Exists(startFolder)) Directory.Delete(startFolder, true);
    }
}
