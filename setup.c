#include <windows.h>
#include <shlobj.h>
#include <objbase.h>
#include <dwmapi.h>
#include <uxtheme.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#pragma comment(lib, "msimg32.lib")

#define ID_BTN_INSTALL   101
#define ID_BTN_UNINSTALL 102
#define ID_BTN_LAUNCH    103
#define ID_EDIT_LOG      104

#define WM_APPEND_LOG    (WM_USER + 1)
#define WM_INSTALL_DONE  (WM_USER + 2)

#ifndef DWMWA_USE_IMMERSIVE_DARK_MODE
#define DWMWA_USE_IMMERSIVE_DARK_MODE 20
#endif

HWND hTitle, hSub, hEditLog, hBtnInstall, hBtnUninstall, hBtnLaunch;
HFONT hFontTitle, hFontMain, hFontBtn, hFontLog;
HBRUSH hBrushLog = NULL;

int progressPct = 0;
BOOL isInstalling = FALSE;
BOOL installSuccess = FALSE;

COLORREF GetBgTop()      { return RGB(28, 28, 32); }
COLORREF GetBgBot()      { return RGB(14, 14, 18); }
COLORREF GetCardBg()     { return RGB(38, 38, 42); }
COLORREF GetAccent()     { return RGB(0, 210, 235); }
COLORREF GetGreen()      { return RGB(52, 199, 89); }
COLORREF GetRed()        { return RGB(255, 59, 48); }

void AppendLogAsync(HWND hwnd, const char* msg) {
    char* copy = _strdup(msg);
    if (copy) PostMessageA(hwnd, WM_APPEND_LOG, 0, (LPARAM)copy);
}

void GetInstallDir(char* outDir) {
    char localAppData[MAX_PATH];
    if (FAILED(SHGetFolderPathA(NULL, CSIDL_LOCAL_APPDATA, NULL, 0, localAppData))) {
        GetCurrentDirectoryA(MAX_PATH, localAppData);
    }
    snprintf(outDir, MAX_PATH, "%s\\Programs\\Siri", localAppData);
}

void CreateDirRecursive(const char* path) {
    char tmp[MAX_PATH];
    strncpy(tmp, path, MAX_PATH - 1);
    tmp[MAX_PATH - 1] = '\0';
    for (char* p = tmp + 1; *p; p++) {
        if (*p == '\\' || *p == '/') {
            *p = '\0';
            CreateDirectoryA(tmp, NULL);
            *p = '\\';
        }
    }
    CreateDirectoryA(tmp, NULL);
}

void CreateShortcut(const char* targetPath, const char* args, const char* workDir, const char* shortcutPath, const char* iconPath) {
    IShellLinkA* psl = NULL;
    if (SUCCEEDED(CoCreateInstance(&CLSID_ShellLink, NULL, CLSCTX_INPROC_SERVER, &IID_IShellLinkA, (LPVOID*)&psl))) {
        psl->lpVtbl->SetPath(psl, targetPath);
        if (args) psl->lpVtbl->SetArguments(psl, args);
        if (workDir) psl->lpVtbl->SetWorkingDirectory(psl, workDir);
        psl->lpVtbl->SetDescription(psl, "Siri iOS 27 Style Assistant");
        if (iconPath && GetFileAttributesA(iconPath) != INVALID_FILE_ATTRIBUTES) {
            psl->lpVtbl->SetIconLocation(psl, iconPath, 0);
        }

        IPersistFile* ppf = NULL;
        if (SUCCEEDED(psl->lpVtbl->QueryInterface(psl, &IID_IPersistFile, (LPVOID*)&ppf))) {
            WCHAR wsz[MAX_PATH];
            MultiByteToWideChar(CP_ACP, 0, shortcutPath, -1, wsz, MAX_PATH);
            ppf->lpVtbl->Save(ppf, wsz, TRUE);
            ppf->lpVtbl->Release(ppf);
        }
        psl->lpVtbl->Release(psl);
    }
}

DWORD WINAPI InstallThread(LPVOID lpParam) {
    HWND hwnd = (HWND)lpParam;
    CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);

    char srcDir[MAX_PATH], dstDir[MAX_PATH];
    GetModuleFileNameA(NULL, srcDir, MAX_PATH);
    char* slash = strrchr(srcDir, '\\');
    if (slash) *slash = '\0';

    GetInstallDir(dstDir);

    progressPct = 15;
    InvalidateRect(hBtnInstall, NULL, FALSE);
    AppendLogAsync(hwnd, "[1/4] Creating installation folder...\r\n");
    CreateDirRecursive(dstDir);
    Sleep(300);

    // 1. Copia siri.py e icona
    char srcPy[MAX_PATH], dstPy[MAX_PATH];
    snprintf(srcPy, MAX_PATH, "%s\\siri.py", srcDir);
    snprintf(dstPy, MAX_PATH, "%s\\siri.py", dstDir);

    if (!CopyFileA(srcPy, dstPy, FALSE)) {
        AppendLogAsync(hwnd, "[ERROR] siri.py not found next to the installer!\r\n");
        installSuccess = FALSE;
        PostMessageA(hwnd, WM_INSTALL_DONE, 0, 0);
        CoUninitialize();
        return 1;
    }

    char srcIcon[MAX_PATH], dstIcon[MAX_PATH];
    snprintf(srcIcon, MAX_PATH, "%s\\icon.ico", srcDir);
    snprintf(dstIcon, MAX_PATH, "%s\\icon.ico", dstDir);
    CopyFileA(srcIcon, dstIcon, FALSE);

    snprintf(srcIcon, MAX_PATH, "%s\\icon.png", srcDir);
    snprintf(dstIcon, MAX_PATH, "%s\\icon.png", dstDir);
    CopyFileA(srcIcon, dstIcon, FALSE);

    progressPct = 35;
    InvalidateRect(hBtnInstall, NULL, FALSE);
    AppendLogAsync(hwnd, "[2/4] Application files copied.\r\n");

    // Rileva il percorso reale di pythonw.exe (compatibile anche con Python del Microsoft Store)
    char pythonwPath[MAX_PATH] = "pythonw.exe";
    FILE* fpWhere = _popen("where pythonw.exe 2>nul", "r");
    if (fpWhere) {
        if (fgets(pythonwPath, MAX_PATH, fpWhere)) {
            size_t len = strlen(pythonwPath);
            while (len > 0 && (pythonwPath[len - 1] == '\n' || pythonwPath[len - 1] == '\r')) {
                pythonwPath[--len] = '\0';
            }
        }
        _pclose(fpWhere);
    }

    char argPy[MAX_PATH + 16];
    snprintf(argPy, sizeof(argPy), "\"%s\\siri.py\"", dstDir);

    char desktopDir[MAX_PATH], startMenuDir[MAX_PATH], lnkDesktop[MAX_PATH], lnkStart[MAX_PATH], icoUse[MAX_PATH];
    snprintf(icoUse, MAX_PATH, "%s\\icon.ico", dstDir);

    if (SUCCEEDED(SHGetFolderPathA(NULL, CSIDL_DESKTOPDIRECTORY, NULL, 0, desktopDir))) {
        snprintf(lnkDesktop, MAX_PATH, "%s\\Siri.lnk", desktopDir);
        CreateShortcut(pythonwPath, argPy, dstDir, lnkDesktop, icoUse);
    }
    if (SUCCEEDED(SHGetFolderPathA(NULL, CSIDL_PROGRAMS, NULL, 0, startMenuDir))) {
        snprintf(lnkStart, MAX_PATH, "%s\\Siri.lnk", startMenuDir);
        CreateShortcut(pythonwPath, argPy, dstDir, lnkStart, icoUse);
    }

    // 3. Controlla se Python 3 è installato; se manca, lo installa tramite winget
    progressPct = 45;
    InvalidateRect(hBtnInstall, NULL, FALSE);
    AppendLogAsync(hwnd, "[3/5] Checking Python 3 installation...\r\n");

    int hasPython = system("python --version >nul 2>&1");
    if (hasPython != 0) {
        AppendLogAsync(hwnd, "[INFO] Python 3 not found. Installing Python 3.12 automatically via winget...\r\n");
        int wingetRes = system("winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1");
        if (wingetRes != 0) {
            AppendLogAsync(hwnd, "[ERROR] Automatic Python installation failed.\r\nPlease install Python 3 manually from python.org and run Setup again.\r\n");
            ShellExecuteA(NULL, "open", "https://python.org", NULL, NULL, SW_SHOWNORMAL);
            installSuccess = FALSE;
            PostMessageA(hwnd, WM_INSTALL_DONE, 0, 0);
            CoUninitialize();
            return 1;
        }
        AppendLogAsync(hwnd, "[OK] Python 3.12 installed!\r\n");
    } else {
        AppendLogAsync(hwnd, "[OK] Python 3 is already installed.\r\n");
    }

    // 4. Installa PyQt6 tramite pip (usando py -m pip o python -m pip)
    progressPct = 65;
    InvalidateRect(hBtnInstall, NULL, FALSE);
    AppendLogAsync(hwnd, "[4/5] Installing PyQt6 dependency (please wait)...\r\n");

    SECURITY_ATTRIBUTES sa = { sizeof(sa), NULL, TRUE };
    HANDLE hRead, hWrite;
    CreatePipe(&hRead, &hWrite, &sa, 0);
    SetHandleInformation(hRead, HANDLE_FLAG_INHERIT, 0);

    STARTUPINFOA si = { sizeof(si) };
    PROCESS_INFORMATION pi = { 0 };
    si.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;
    si.hStdOutput = hWrite;
    si.hStdError = hWrite;

    char pipCmd[] = "cmd.exe /c python -m pip install PyQt6 --quiet";
    if (CreateProcessA(NULL, pipCmd, NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, dstDir, &si, &pi)) {
        CloseHandle(hWrite);
        char buf[256];
        DWORD readBytes;
        while (ReadFile(hRead, buf, sizeof(buf) - 1, &readBytes, NULL) && readBytes > 0) {
            buf[readBytes] = '\0';
            AppendLogAsync(hwnd, buf);
        }
        WaitForSingleObject(pi.hProcess, INFINITE);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    } else {
        CloseHandle(hWrite);
    }
    CloseHandle(hRead);

    // 4. Crea collegamenti su Desktop e Menu Start
    progressPct = 85;
    InvalidateRect(hBtnInstall, NULL, FALSE);
    AppendLogAsync(hwnd, "[4/4] Creating Desktop and Start Menu shortcuts...\r\n");

    progressPct = 100;
    installSuccess = TRUE;
    AppendLogAsync(hwnd, "\r\n[DONE] Siri has been installed successfully!\r\n");
    PostMessageA(hwnd, WM_INSTALL_DONE, 0, 0);

    CoUninitialize();
    return 0;
}

void RunUninstall(HWND hwnd) {
    char dstDir[MAX_PATH], desktopDir[MAX_PATH], startMenuDir[MAX_PATH], linkPath[MAX_PATH];
    GetInstallDir(dstDir);

    if (SUCCEEDED(SHGetFolderPathA(NULL, CSIDL_DESKTOPDIRECTORY, NULL, 0, desktopDir))) {
        snprintf(linkPath, MAX_PATH, "%s\\Siri.lnk", desktopDir);
        DeleteFileA(linkPath);
    }
    if (SUCCEEDED(SHGetFolderPathA(NULL, CSIDL_PROGRAMS, NULL, 0, startMenuDir))) {
        snprintf(linkPath, MAX_PATH, "%s\\Siri.lnk", startMenuDir);
        DeleteFileA(linkPath);
    }

    char pathDoubleNull[MAX_PATH + 2] = { 0 };
    strncpy(pathDoubleNull, dstDir, MAX_PATH - 1);
    SHFILEOPSTRUCTA op = { 0 };
    op.wFunc = FO_DELETE;
    op.pFrom = pathDoubleNull;
    op.fFlags = FOF_NOCONFIRMATION | FOF_NOERRORUI | FOF_SILENT;
    SHFileOperationA(&op);

    SetWindowTextA(hEditLog, "[UNINSTALLED] Siri and its shortcuts have been removed.\r\n");
    ShowWindow(hBtnLaunch, SW_HIDE);
}

LRESULT CALLBACK WindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
        case WM_CREATE: {
            BOOL dark = TRUE;
            DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, &dark, sizeof(dark));

            hFontTitle = CreateFontA(24, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE,
                DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH, "Segoe UI");
            hFontMain = CreateFontA(14, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
                DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH, "Segoe UI");
            hFontBtn = CreateFontA(14, 0, 0, 0, FW_SEMIBOLD, FALSE, FALSE, FALSE,
                DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH, "Segoe UI");
            hFontLog = CreateFontA(13, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
                DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, FIXED_PITCH, "Consolas");

            hBrushLog = CreateSolidBrush(GetCardBg());

            hTitle = CreateWindowA("STATIC", "Siri Setup",
                WS_VISIBLE | WS_CHILD | SS_LEFT, 25, 20, 380, 30, hwnd, NULL, NULL, NULL);
            SendMessage(hTitle, WM_SETFONT, (WPARAM)hFontTitle, TRUE);

            hSub = CreateWindowA("STATIC", "iOS 27 Style Assistant for Windows  •  by claimy17",
                WS_VISIBLE | WS_CHILD | SS_LEFT, 25, 52, 380, 22, hwnd, NULL, NULL, NULL);
            SendMessage(hSub, WM_SETFONT, (WPARAM)hFontMain, TRUE);

            hEditLog = CreateWindowA("EDIT", "Ready to install Siri into your user profile.\r\nClick Install to begin.\r\n",
                WS_VISIBLE | WS_CHILD | WS_VSCROLL | ES_MULTILINE | ES_AUTOVSCROLL | ES_READONLY,
                25, 86, 385, 165, hwnd, (HMENU)ID_EDIT_LOG, NULL, NULL);
            SendMessage(hEditLog, WM_SETFONT, (WPARAM)hFontLog, TRUE);
            SetWindowTheme(hEditLog, L"DarkMode_Explorer", NULL);

            RECT rcLog;
            GetClientRect(hEditLog, &rcLog);
            HRGN hRgnLog = CreateRoundRectRgn(0, 0, rcLog.right + 1, rcLog.bottom + 1, 14, 14);
            SetWindowRgn(hEditLog, hRgnLog, TRUE);

            hBtnInstall = CreateWindowA("BUTTON", "Install Siri",
                WS_VISIBLE | WS_CHILD | BS_OWNERDRAW, 25, 268, 255, 42, hwnd, (HMENU)ID_BTN_INSTALL, NULL, NULL);
            SendMessage(hBtnInstall, WM_SETFONT, (WPARAM)hFontBtn, TRUE);

            hBtnUninstall = CreateWindowA("BUTTON", "Uninstall",
                WS_VISIBLE | WS_CHILD | BS_OWNERDRAW, 290, 268, 120, 42, hwnd, (HMENU)ID_BTN_UNINSTALL, NULL, NULL);
            SendMessage(hBtnUninstall, WM_SETFONT, (WPARAM)hFontBtn, TRUE);

            hBtnLaunch = CreateWindowA("BUTTON", "Launch Siri Now",
                WS_CHILD | BS_OWNERDRAW, 25, 268, 385, 42, hwnd, (HMENU)ID_BTN_LAUNCH, NULL, NULL);
            SendMessage(hBtnLaunch, WM_SETFONT, (WPARAM)hFontBtn, TRUE);
            break;
        }

        case WM_ERASEBKGND: {
            HDC hdc = (HDC)wParam;
            RECT rc;
            GetClientRect(hwnd, &rc);

            TRIVERTEX v[2];
            v[0].x = 0; v[0].y = 0;
            v[0].Red = GetRValue(GetBgTop()) << 8; v[0].Green = GetGValue(GetBgTop()) << 8; v[0].Blue = GetBValue(GetBgTop()) << 8; v[0].Alpha = 0;
            v[1].x = rc.right; v[1].y = rc.bottom;
            v[1].Red = GetRValue(GetBgBot()) << 8; v[1].Green = GetGValue(GetBgBot()) << 8; v[1].Blue = GetBValue(GetBgBot()) << 8; v[1].Alpha = 0;

            GRADIENT_RECT gRect = { 0, 1 };
            GradientFill(hdc, v, 2, &gRect, 1, GRADIENT_FILL_RECT_V);
            return 1;
        }

        case WM_CTLCOLORSTATIC: {
            HDC hdc = (HDC)wParam;
            HWND hCtrl = (HWND)lParam;
            if (hCtrl == hEditLog) {
                SetTextColor(hdc, RGB(235, 235, 240));
                SetBkColor(hdc, GetCardBg());
                return (LRESULT)hBrushLog;
            }
            SetTextColor(hdc, (hCtrl == hTitle) ? RGB(255, 255, 255) : RGB(160, 160, 170));
            SetBkMode(hdc, TRANSPARENT);
            return (LRESULT)GetStockObject(NULL_BRUSH);
        }
        case WM_DRAWITEM: {
            LPDRAWITEMSTRUCT dis = (LPDRAWITEMSTRUCT)lParam;
            if (dis->CtlType == ODT_BUTTON) {
                HDC hdc = dis->hDC;
                RECT rc = dis->rcItem;

                POINT pt = { 0, 0 };
                MapWindowPoints(dis->hwndItem, hwnd, &pt, 1);
                SetViewportOrgEx(hdc, -pt.x, -pt.y, NULL);
                SendMessage(hwnd, WM_ERASEBKGND, (WPARAM)hdc, 0);
                SetViewportOrgEx(hdc, 0, 0, NULL);

                UINT id = dis->CtlID;
                int radius = 18;

                if (id == ID_BTN_INSTALL && isInstalling) {
                    HRGN rgn = CreateRoundRectRgn(rc.left, rc.top, rc.right + 1, rc.bottom + 1, radius, radius);
                    SelectClipRgn(hdc, rgn);

                    HBRUSH brGray = CreateSolidBrush(RGB(65, 65, 70));
                    FillRect(hdc, &rc, brGray);
                    DeleteObject(brGray);

                    int w = ((rc.right - rc.left) * progressPct) / 100;
                    if (w > 0) {
                        RECT rcFill = rc;
                        rcFill.right = rc.left + w;
                        HBRUSH brGreen = CreateSolidBrush(GetGreen());
                        FillRect(hdc, &rcFill, brGreen);
                        DeleteObject(brGreen);
                    }
                    SelectClipRgn(hdc, NULL);
                    DeleteObject(rgn);

                    char buf[64];
                    snprintf(buf, sizeof(buf), "INSTALLING... %d%%", progressPct);
                    SetBkMode(hdc, TRANSPARENT);
                    SetTextColor(hdc, RGB(255, 255, 255));
                    DrawTextA(hdc, buf, -1, &rc, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
                    return TRUE;
                }

                COLORREF bg = (id == ID_BTN_INSTALL) ? GetAccent() : (id == ID_BTN_LAUNCH ? GetGreen() : RGB(58, 58, 64));
                COLORREF fg = (id == ID_BTN_INSTALL) ? RGB(0, 0, 0) : RGB(255, 255, 255);

                HBRUSH br = CreateSolidBrush(bg);
                HPEN pn = CreatePen(PS_SOLID, 1, bg);
                HGDIOBJ oldB = SelectObject(hdc, br);
                HGDIOBJ oldP = SelectObject(hdc, pn);
                RoundRect(hdc, rc.left, rc.top, rc.right, rc.bottom, radius, radius);
                SelectObject(hdc, oldB);
                SelectObject(hdc, oldP);
                DeleteObject(br);
                DeleteObject(pn);

                char txt[64];
                GetWindowTextA(dis->hwndItem, txt, sizeof(txt));
                SetBkMode(hdc, TRANSPARENT);
                SetTextColor(hdc, fg);
                DrawTextA(hdc, txt, -1, &rc, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
                return TRUE;
            }
            break;
        }

        case WM_APPEND_LOG: {
            char* text = (char*)lParam;
            if (text) {
                int len = GetWindowTextLengthA(hEditLog);
                SendMessageA(hEditLog, EM_SETSEL, (WPARAM)len, (LPARAM)len);
                SendMessageA(hEditLog, EM_REPLACESEL, FALSE, (LPARAM)text);
                free(text);
            }
            break;
        }
        case WM_INSTALL_DONE: {
            isInstalling = FALSE;
            EnableWindow(hBtnInstall, TRUE);
            EnableWindow(hBtnUninstall, TRUE);
            if (installSuccess) {
                ShowWindow(hBtnInstall, SW_HIDE);
                ShowWindow(hBtnUninstall, SW_HIDE);
                ShowWindow(hBtnLaunch, SW_SHOW);
            }
            InvalidateRect(hwnd, NULL, TRUE);
            break;
        }

        case WM_COMMAND: {
            int id = LOWORD(wParam);
            if (id == ID_BTN_INSTALL && !isInstalling) {
                SetWindowTextA(hEditLog, "");
                isInstalling = TRUE;
                progressPct = 5;
                EnableWindow(hBtnInstall, FALSE);
                EnableWindow(hBtnUninstall, FALSE);
                InvalidateRect(hBtnInstall, NULL, FALSE);
                HANDLE hT = CreateThread(NULL, 0, InstallThread, hwnd, 0, NULL);
                if (hT) CloseHandle(hT);
            } else if (id == ID_BTN_UNINSTALL && !isInstalling) {
                RunUninstall(hwnd);
            } else if (id == ID_BTN_LAUNCH) {
                char dstDir[MAX_PATH], argPy[MAX_PATH + 16];
                GetInstallDir(dstDir);
                snprintf(argPy, sizeof(argPy), "\"%s\\siri.py\"", dstDir);
                ShellExecuteA(NULL, "open", "pythonw.exe", argPy, dstDir, SW_SHOWNORMAL);
                PostQuitMessage(0);
            }
            break;
        }

        case WM_DESTROY:
            if (hBrushLog) DeleteObject(hBrushLog);
            DeleteObject(hFontTitle);
            DeleteObject(hFontMain);
            DeleteObject(hFontBtn);
            DeleteObject(hFontLog);
            PostQuitMessage(0);
            break;

        default:
            return DefWindowProcA(hwnd, uMsg, wParam, lParam);
    }
    return 0;
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);

    WNDCLASSA wc = { 0 };
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = "SiriSetupWin32";
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hIcon = (HICON)LoadImageA(hInstance, MAKEINTRESOURCEA(1), IMAGE_ICON, 32, 32, LR_DEFAULTCOLOR);
    RegisterClassA(&wc);

    HWND hwnd = CreateWindowExA(
        WS_EX_APPWINDOW, "SiriSetupWin32", "Siri Setup",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT, 445, 365,
        NULL, NULL, hInstance, NULL
    );

    if (!hwnd) return 0;
    ShowWindow(hwnd, nCmdShow);

    MSG msg = { 0 };
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    CoUninitialize();
    return 0;
}
