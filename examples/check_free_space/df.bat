@echo off
chcp 1251 > nul
for /f "tokens=3 delims= " %%A in ('dir /s/-c ^|find "байт свободно"') do (
echo %%A
)
chcp 866 > nul