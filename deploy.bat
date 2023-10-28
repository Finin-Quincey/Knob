@echo off
echo Flashing project to Pico...
for /F %%i in ('ampy ls') do (
    echo Deleting %%i
    ampy rm %%i
)
for %%d in (.\\src\\main\\common, .\\src\\main\\device, .\\lib\\device) do (
    pushd %%d
    for /R %%f in (*.py) do (
        echo Writing %%f
        ampy put "%%f" "%%~nxf"
    )
    popd
)
echo Upload done, rebooting Pico...
ampy reset --hard