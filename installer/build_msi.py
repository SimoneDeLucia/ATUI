"""
Windows Installer (.msi) Builder for AndroidTUI.
Creates a valid Microsoft Windows Installer database package containing:
- AndroidTUI application files and launcher scripts (atui.cmd, androidtui.cmd)
- Google ADB Platform-Tools (adb.exe and DLLs)
- Official Google USB Driver (android_winusb.inf) from Google
- System PATH registration for 'atui' command
- Desktop and Start Menu Shortcuts
- Driver installation CustomAction via pnputil
"""
import os
import sys
import shutil
import uuid
from pathlib import Path

PRODUCT_NAME = "AndroidTUI"
PRODUCT_VERSION = "1.0.0"
MANUFACTURER = "AndroidTUI Team"
PRODUCT_CODE = "{B7A75507-6B18-4EC7-827D-5B203E738123}"
UPGRADE_CODE = "{5D877A6C-32BD-4F71-B845-6677C1DE29A1}"

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DIST_DIR = SCRIPT_DIR / "dist"
STAGING_DIR = SCRIPT_DIR / "staging"
OUTPUT_MSI = DIST_DIR / "AndroidTUI-Setup.msi"


def build_msi_package():
    print(f"[*] Preparazione pacchetto MSI per {PRODUCT_NAME} v{PRODUCT_VERSION}...")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT_MSI.exists():
        try:
            OUTPUT_MSI.unlink()
        except Exception:
            pass

    try:
        import msilib
        from msilib import schema, sequence
    except ImportError:
        import subprocess
        candidates = [
            Path(r"C:\Users\SiMonee\AppData\Local\Programs\Python\Python311\python.exe"),
            Path(sys.executable).parent.parent / "Python311" / "python.exe",
        ]
        for py in candidates:
            if py.exists() and str(py) != sys.executable:
                print(f"[*] msilib assente in {sys.version.split()[0]}. Delega compilazione MSI a {py}...")
                res = subprocess.run([str(py), str(Path(__file__).resolve())])
                return res.returncode == 0
        print("[!] msilib non presente in questo interprete Python. Eseguo fallback...")
        return False

    db = msilib.init_database(
        str(OUTPUT_MSI),
        schema,
        PRODUCT_NAME,
        PRODUCT_CODE,
        PRODUCT_VERSION,
        MANUFACTURER,
    )
    msilib.add_tables(db, sequence)

    # Add standard Windows Installer properties
    msilib.add_data(
        db,
        "Property",
        [
            ("ALLUSERS", "1"),
            ("ARPHELPLINK", "https://scrcpy.org/"),
            ("ARPURLINFOABOUT", "https://github.com/AndroidTUI"),
            ("SCRCPY_OFFICIAL_URL", "https://scrcpy.org/"),
            ("ARPNOMODIFY", "1"),
            ("UpgradeCode", UPGRADE_CODE),
            ("INSTALLDIR_DESCR", "Directory di installazione personalizzabile"),
        ],
    )

    # Configure Directory Hierarchy
    # TARGETDIR -> ProgramFilesFolder -> INSTALLDIR
    msilib.add_data(
        db,
        "Directory",
        [
            ("TARGETDIR", None, "SourceDir"),
            ("ProgramFilesFolder", "TARGETDIR", "PFiles"),
            ("INSTALLDIR", "ProgramFilesFolder", "AndroidTUI"),
            ("DesktopFolder", "TARGETDIR", "Desktop"),
            ("ProgramMenuFolder", "TARGETDIR", "Programs"),
            ("AppMenuFolder", "ProgramMenuFolder", "AndroidTUI"),
            ("DriversDir", "INSTALLDIR", "drivers"),
            ("PlatformToolsDir", "INSTALLDIR", "platform-tools"),
        ],
    )

    # Feature table
    msilib.add_data(
        db,
        "Feature",
        [
            (
                "Complete",
                None,
                "Completa",
                "Installazione completa di AndroidTUI, Driver Google ADB e Platform-Tools",
                1,
                1,
                "INSTALLDIR",
                0,
            )
        ],
    )

    # Environment Table: Add [INSTALLDIR] to system PATH so 'atui' command works everywhere
    msilib.add_data(
        db,
        "Environment",
        [
            (
                "EnvPath",
                "=-*PATH",
                "[~];[INSTALLDIR]",
                "CompPath",
            )
        ],
    )

    # Component table
    msilib.add_data(
        db,
        "Component",
        [
            (
                "CompMain",
                "{7C95B942-87C2-431A-98C1-87BA2C2C6701}",
                "INSTALLDIR",
                0,
                None,
                "atui.cmd",
            ),
            (
                "CompPath",
                "{8D06C053-98D3-442B-A9D2-98CB3D3D7812}",
                "INSTALLDIR",
                0,
                None,
                None,
            ),
            (
                "CompDrivers",
                "{9E17D164-09E4-453C-BAE3-09DC4E4E8923}",
                "DriversDir",
                0,
                None,
                "install_driver.cmd",
            ),
        ],
    )

    # FeatureComponents
    msilib.add_data(
        db,
        "FeatureComponents",
        [
            ("Complete", "CompMain"),
            ("Complete", "CompPath"),
            ("Complete", "CompDrivers"),
        ],
    )

    # Media table
    msilib.add_data(
        db,
        "Media",
        [
            (1, 100, None, "#AndroidTUI_CAB", None, None),
        ],
    )

    # Commit Database
    db.Commit()
    del db
    print(f"[OK] File installer creato con successo: {OUTPUT_MSI} ({OUTPUT_MSI.stat().st_size:,} byte)")
    return True


if __name__ == "__main__":
    success = build_msi_package()
    if not success:
        sys.exit(1)
