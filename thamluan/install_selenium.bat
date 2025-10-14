@echo off
echo ===============================================================================
echo INSTALLING SELENIUM + WEBDRIVER MANAGER
echo ===============================================================================
echo.

echo [1/2] Installing Selenium...
pip install selenium
echo.

echo [2/2] Installing WebDriver Manager (auto ChromeDriver)...
pip install webdriver-manager
echo.

echo ===============================================================================
echo ✅ INSTALLATION COMPLETE!
echo ===============================================================================
echo.
echo Next steps:
echo   1. Test crawler: python test_law_crawler_selenium.py
echo   2. Run workflow: python test_hybrid_workflow.py
echo.
pause
