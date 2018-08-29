# encoding:utf-8
#上面这句话不加的话  会报中文识别异常
import os
import os.path
import re
import subprocess
from xml.etree import ElementTree as ET
androidNS = 'http://schemas.android.com/apk/res/android'

curDir = os.getcwd()

def getCurrDir():
	global curDir
	retPath = curDir
	retPath = retPath.decode('gbk')
	return retPath

def getFullPath(filename):
	if os.path.isabs(filename):
		return filename
	currdir = getCurrDir()
	filename = os.path.join(currdir, filename)
	filename = filename.replace('\\', '/')
	filename = re.sub('/+', '/', filename)
	return filename

def getFullToolPath(filename):
	return getFullPath("bin/"+filename)

def getFullOutPutPath(filename):
	return getFullPath("output/"+filename)

def getworkDirPath():
	return getFullPath("workSpace")

def getFullWorkDir(filename):
	return getFullPath("workSpace/"+filename)

def getJavaBinDir():
	return getFullPath("bin/jre/bin/")

def getJavaCMD():
	return getJavaBinDir() + "java"

def execFormatCmd(cmd):
	cmd = cmd.replace('\\', '/')
	cmd = re.sub('/+', '/', cmd)
	ret = 0
	st = subprocess.STARTUPINFO
	st.dwFlags = subprocess.STARTF_USESHOWWINDOW
	st.wShowWindow = subprocess.SW_HIDE
	cmd = str(cmd).encode('gbk')

	s = subprocess.Popen(cmd, shell=True)
	ret = s.wait()
	if ret:
		s = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		cmd = 'ERROR:' + cmd + ' exec Fail'
	else:
		cmd += '  exec success'
	#print(cmd)
	return ret


def del_file_folder(src):
	if os.path.exists(src):
		if os.path.isfile(src):
			try:
				src = src.replace('\\', '/')
				os.remove(src)
			except:
				pass

		elif os.path.isdir(src):
			for item in os.listdir(src):
				itemsrc = os.path.join(src, item)
				del_file_folder(itemsrc)

			try:
				os.rmdir(src)
			except:
				pass

def copy_files(src, dest):
    if not os.path.exists(src):
        printF("copy files . the src is not exists.path:%s", src)
        return

    if os.path.isfile(src):
        copy_file(src, dest)
        return

    for f in os.listdir(src):
        sourcefile = os.path.join(src, f)
        targetfile = os.path.join(dest, f)
        if os.path.isfile(sourcefile):
            copy_file(sourcefile, targetfile)
        else:
            copy_files(sourcefile, targetfile)

def copy_file(src, dest):
	sourcefile = getFullPath(src)
	destfile = getFullPath(dest)
	if not os.path.exists(sourcefile):
		return
	if not os.path.exists(destfile) or os.path.getsize(destfile) != os.path.getsize(sourcefile):
		destdir = os.path.dirname(destfile)
		if not os.path.exists(destdir):
			os.makedirs(destdir)
		destfilestream = open(destfile, 'wb')
		sourcefilestream = open(sourcefile, 'rb')
		destfilestream.write(sourcefilestream.read())
		destfilestream.close()
		sourcefilestream.close()

#修改包名
def renamePackageName(targetdir, newPackageName):
	manifestFile = targetdir + "/AndroidManifest.xml"
	manifestFile = getFullPath(manifestFile)
	ET.register_namespace('android', androidNS)
	tree = ET.parse(manifestFile)
	root = tree.getroot()
	package = root.attrib.get('package')

	oldPackageName = package
	if newPackageName[0:1] == '.':
		newPackageName = oldPackageName + newPackageName

	#检查并修改所有activity的相对路径及包名
	appNode = root.find('application')
	if appNode != None:
		activityLst = appNode.findall('activity')
		key = '{'+androidNS+'}name'
		if activityLst != None and len(activityLst) > 0:
			for aNode in activityLst:
				activityName = aNode.attrib[key]
				if activityName[0:1] == '.':
					activityName = oldPackageName + activityName
				elif activityName.find('.') == -1:
					activityName = oldPackageName + '.' + activityName
				aNode.attrib[key] = activityName

		serviceLst = appNode.findall('service')
		key = '{'+androidNS+'}name'
		if serviceLst != None and len(serviceLst) > 0:
			for sNode in serviceLst:
				serviceName = sNode.attrib[key]
				if serviceName[0:1] == '.':
					serviceName = oldPackageName + serviceName
				elif serviceName.find('.') == -1:
					serviceName = oldPackageName + '.' + serviceName
				sNode.attrib[key] = serviceName

	root.attrib['package'] = newPackageName
	tree.write(manifestFile, 'UTF-8')

	package = newPackageName
	return package

#生成R文件
def generateNewRFile(newPackageName, decompileDir):
	decompileDir = getFullPath(decompileDir)
	tempPath = os.path.dirname(decompileDir)
	tempPath = tempPath + "/temp"
	if os.path.exists(tempPath):
		del_file_folder(tempPath)
	if not os.path.exists(tempPath):
		os.makedirs(tempPath)

	resPath = os.path.join(decompileDir, "res")
	targetResPath = os.path.join(tempPath, "res")
	copy_files(resPath, targetResPath)

	genPath = os.path.join(tempPath, "gen")
	if not os.path.exists(genPath):
		os.makedirs(genPath)

	aaptPath = getFullToolPath("aapt")

	androidPath = getFullToolPath("android.jar")
	manifestPath = os.path.join(decompileDir, "AndroidManifest.xml")
	cmd = '"%s" p -f -m -J "%s" -S "%s" -I "%s" -M "%s"' % (aaptPath, genPath, targetResPath, androidPath, manifestPath)
	ret = execFormatCmd(cmd)
	if ret:
		return 1

	rPath = newPackageName.replace('.', '/')
	rPath = os.path.join(genPath, rPath)
	rPath = os.path.join(rPath, "R.java")

	cmd = '"%sjavac" -source 1.7 -target 1.7 -encoding UTF-8 "%s"' % (getJavaBinDir(), rPath)
	ret = execFormatCmd(cmd)
	if ret:
		return 1

	targetDexPath = os.path.join(tempPath, "classes.dex")
	dexToolPath = getFullToolPath("dx.bat")

	cmd = '"%s" --dex --output="%s" "%s"' % (dexToolPath, targetDexPath, genPath)
	ret = execFormatCmd(cmd)
	if ret:
		return 1

	smaliPath = os.path.join(decompileDir, "smali")
	ret = dex2smali(targetDexPath, smaliPath, "baksmali.jar")

	return ret

#smali生成新的smali文件
def dex2smali(dexFile, targetdir, dextool = "baksmali.jar"):
	if not os.path.exists(dexFile):
		print("dex2smali : the dexFile is not exists. path:%s", dexFile)
		return

	if not os.path.exists(targetdir):
		os.makedirs(targetdir)

	dexFile = getFullPath(dexFile)
	smaliTool = getFullToolPath(dextool)
	targetdir = getFullPath(targetdir)

	cmd = '"%s" -jar "%s" -o "%s" "%s"' % (getJavaCMD(), smaliTool, targetdir, dexFile)

	ret = execFormatCmd(cmd)

	return ret

#压包
def recompileApk(sourcefolder, apkfile, apktool = "apktool.jar"):

	os.chdir(curDir)
	sourcefolder = getFullPath(sourcefolder)
	apkfile = getFullPath(apkfile)
	apktool = getFullToolPath(apktool)

	ret = 1
	if os.path.exists(sourcefolder):
		cmd = '"%s" -jar "%s" -q b -f "%s" -o "%s"' % (getJavaCMD(), apktool, sourcefolder, apkfile)
		ret = execFormatCmd(cmd)

	return ret


def signApk(keystore, apkfile):
	print "keystore="+str(keystore)
	signApkFinal(apkfile, keystore['keystore'], keystore['password'], keystore['aliaskey'], keystore['aliaspwd'])

def signApkFinal(apkfile, keystore, password, alias, aliaspwd):

	if not os.path.exists(keystore):
		return 1
	apkfile = getFullPath(apkfile)
	keystore = getFullPath(keystore)
	aapt = getFullToolPath("aapt")

	listcmd = '%s list %s' % (aapt, apkfile)
	listcmd = listcmd.encode('gb2312')
	output = os.popen(listcmd).read()
	for filename in output.split('\n'):
		if filename.find('META_INF') == 0:
			rmcmd = '"%s" remove "%s" "%s"' % (aapt, apkfile, filename)
			execFormatCmd(rmcmd)

	signcmd = '"%sjarsigner" -keystore "%s" -storepass "%s" -keypass "%s" "%s" "%s" -sigalg SHA1withRSA -digestalg SHA1' % (getJavaBinDir(),
			keystore, password, aliaspwd, apkfile, alias)

	ret = execFormatCmd(signcmd)

	return ret

#对齐
def alignApk(apkfile, targetapkfile):
	align = getFullToolPath('zipalign')
	aligncmd = '"%s" -f 4 "%s" "%s"' % (align, apkfile, targetapkfile)
	ret = execFormatCmd(aligncmd)
	return ret