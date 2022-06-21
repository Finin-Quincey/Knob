@echo off
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
            echo Writing %%f
            ampy put "%%f" "%%~nxf"
        )
    )
    popd
)
echo Upload done