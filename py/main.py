# encoding:utf-8
#上面这句话不加的话  会报中文识别异常

import sys
import utils
import os
from xml.etree import ElementTree as ET
androidNS = 'http://schemas.android.com/apk/res/android'
if __name__=="__main__":
	print("welcome to python 2.7.3")
	#解析配置文件
	configFile = utils.getFullPath("config/config.xml")
	try:
		configTree = ET.parse(configFile)
		configRoot = configTree.getroot()
	except Exception, e:
		print("can not parse xml config on path:%s", configFile)
		exit(0)

	#获取配置的app名称
	apkName = configRoot.find('app').get("value")

	#获取配置的渠道及包名
	channels = configRoot.find('channel').findall('param')
	channelList = []
	for cn in channels:
		channel = {}
		channel['value']=cn.get('value')
		channel['name']=cn.get('name')
		channelList.append(channel)
	print(channelList)
	
	#签名文件
	keyStore = {}
	keyStoreParams = configRoot.find('keyStore').findall('param')
	for param in keyStoreParams:
		keyStore[param.get('name')] = param.get('value')

	for param in channelList:
		channelName = param.get('name')
		channelPack = param.get('value')
		#清空workDir 及 apktool的1.apk文件
		sourcepath = utils.getFullPath(apkName)
		workDir = utils.getFullWorkDir(channelName)
		utils.del_file_folder(workDir)
		apktool_workpath=os.path.expanduser('~')+'/apktool/framework/1.apk'
		utils.del_file_folder(apktool_workpath)

		#apk 拷贝工作目录
		apkfile = workDir + "/temp.apk"
		apkfile = utils.getFullPath(apkfile)
		utils.copy_file(sourcepath, apkfile)

		#apk 解压目录
		targetdir = workDir + "/decompile"
		targetdir = utils.getFullPath(targetdir)	
		
		apktool = utils.getFullToolPath("apktool.jar")

		# 清空和创建解压目录
		if os.path.exists(targetdir):
			utils.del_file_folder(targetdir)
		if not os.path.exists(targetdir):
			os.makedirs(targetdir)
		cmd = '"%s" -jar "%s" -q d -d -f "%s" -o "%s"' % (utils.getJavaCMD(), apktool, apkfile, targetdir)
		ret = utils.execFormatCmd(cmd)
		#ret 返回0,表示解压成功
		if ret:
			print("decompile apk failed and process stoped")
			exit(0)
		#修改AndroidManifest.xml文件
	
		#修改包名
		newPackageName = utils.renamePackageName(targetdir,channelPack)
		#重新压smali生成新的R文件
		utils.generateNewRFile(newPackageName,targetdir)
		#重新编译apk
		targetApk = workDir + "/target.apk"
		ret = utils.recompileApk(targetdir, targetApk)
		#重新签名
		utils.signApk(keyStore,targetApk)
		#输出文件夹
		outputFile = utils.getFullOutPutPath(channelName+'.apk')
		#对齐
		ret = utils.alignApk(targetApk, outputFile)


