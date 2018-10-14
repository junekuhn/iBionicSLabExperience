# Aruco Setup Instructions

1. Make sure Windows is up to date
2. Ensure Python 2.7 x64 is installed and on the path and OpenCV 3.2.0 is installed.
3. Install Visual Studio with C++
4. Install [CMake](http://www.cmake.org/download/)
4. Make a folder on your desktop called OpenCV
5. Download [OpenCV](https://github.com/opencv/opencv) and [OpenCV Contrib](https://github.com/opencv/opencv_contrib) and extract it to your OpenCV folder on the desktop
6. Delete everything except aruco in the modules folder
7. Open CMake, and click configure
8. Select Visual Studio 15 2017 Win64 and Specify native compilers
9. For C and C++, go to the Visual Studio installation directory and find cl.exe Path: `<Visual Studio>/VC/Tools/MSVC/14.10.25017/bin/HostX64/x64/cl.exe`
10. Fill in Source Code: `C:/Users/<username>/Desktop/OpenCV/opencv-master`
11. Fill in Build Binaries: `C:/Users/<username>/Desktop/OpenCV/opencv-master/build`
12. Click configure
13. Set the following values:
 - OPENCV_EXTRA_MODULES_PATH=C:/Users/<user>/Desktop/OpenCV/opencv_contrib-master/modules
 - PYTHON2_EXECUTABLE=C:/Python27/python.exe
 - PYTHON2_INCLUDE_DIR=C:/Python27/include
 - PYTHON2_LIBRARY=C:/Python27/libs/python27.lib
 - PYTHON2_NUMPY_INCLUDE_DIRS=C:/Python27/lib/site-packages/numpy/core/include
 - PYTHON2_PACKAGES_PATH=C:/Python27/Lib/site-packages
 - WITH_OPENNI= Check
 - WITH_OPENNI2= Check
14. Click configure
15. Click generate
16. Click open project
17. Change visual studio into Release and make sure x64 is selected.
18. Right click on CMakeTargets -> Install and click Install
19. Copy .dll files from bin/release and cv2.pyd from build/lib/release to the site-packages folder in C:/Python27/Lib/
