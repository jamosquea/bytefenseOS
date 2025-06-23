# Install WiX Toolset first: https://wixtoolset.org/
# Then create MSI package
$wixPath = "C:\Program Files (x86)\WiX Toolset v3.11\bin"
& "$wixPath\candle.exe" bytefense.wxs
& "$wixPath\light.exe" bytefense.wixobj -o BytefenseOS-1.0.0.msi