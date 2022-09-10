@echo off & setlocal enabledelayedexpansion
echo Flashing project to Pico...
for /F %%i in ('ampy ls') do (
    echo Deleting %%i
    ampy rm %%i
)
for %%d in (.\\src\\main\\common, .\\src\\main\\device, .\\lib\\device) do (
    pushd %%d
    for /R %%f in (*.py) do (
        if /I "%%f"=="%~1" (
            echo Writing %%f as main.py
            ampy put "%%f" "main.py"
        ) else (
            set B=%%f
            set B=!B:%CD%\=!
            echo Writing %%f as !B:\=/!
            ampy put "%%f" !B:\=/!
        )
    )
    popd
)
echo Upload done