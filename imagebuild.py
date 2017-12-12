#!/usr/bin/env python3
# Under alpine
# apk update
# apk add python3
# pip3 install pyyaml

import os
import yaml
import sys
import re
import subprocess
import errno
import glob
import configparser
from distutils.version import LooseVersion

class ShellConfig:

  def __init__(self):
    self.pattern = r'[ |\t]*([a-zA-Z_][a-zA-Z0-9_]*)=("([^\\"]|.*)"|([^# \t]*)).*[\r]*\n'
    self.prog = re.compile(self.pattern)
 
  def parse_lines(self, lines, dict):

    for line in lines:
      result = self.prog.match(line)
      if not result is None:
        name = result.groups()[0]
        if result.groups()[2] is None:
          value= result.groups()[3]
        else:
          value= result.groups()[2]
      dict[name]=value

    return dict

  def read_shell_config(self, filename, dict=None):
    if dict is None:
      dict={}
    try:
      with open(filename) as f:
        lines = f.readlines()
        self.parse_lines(lines, dict)
    except IOError:
      pass

    return dict

class OsRelease(ShellConfig):
  def __init__(self, filename='/etc/os-release'):
    ShellConfig.__init__(self)
    self.read_shell_config(filename,self.__dict__)

class Locale(ShellConfig):
  def __init__(self, filename='/etc/locale.conf', LANG='en_US.UTF-8'):
    self.LANG=LANG
    ShellConfig.__init__(self)
    self.read_shell_config(filename,self.__dict__)

class DictToObject:
  def __init__(self, dict):
    self.__dict__.update(dict)



class PackageManagerBase:
  def __init__(self):
    pass

  def compare_version(self, a,b):
      if  a == "rawhide":
        va = LooseVersion(str(sys.maxsize))
      else:
        va = LooseVersion(str(a))

      if  b == "rawhide":
        vb = LooseVersion(str(sys.maxsize))
      else:
        vb = LooseVersion(str(b))

      return (va > vb)

  def determine_package_manager(self, os_name, os_version):
    if os_name == "fedora":
      if self.compare_version(os_version, 21): 
        return "dnf"
      else:
        return "yum"

    elif os_name == "centos":
      return "yum"

    elif os_name == "rhel":
      return "yum"

    elif os_name == "debian":
      return "apt-get"

    elif os_name == "alpine":
      return "apk"
    else:
      return ""

  def package_list(self, os_name, os_version):
    if os_name == "fedora":
      if self.compare_version(os_version, 21): 
        list = "bash rootfiles vim-minimal sssd-client e2fsprogs dnf dnf-yum fedora-release"
      else:
        list = "bash rootfiles vim-minimal sssd-client e2fsprogs yum fedora-release"
    elif os_name == "centos":
      list = "bash rootfiles vim-minimal sssd-client e2fsprogs yum systemd centos-release"
    elif os_name == "rhel":
      list = "bash rootfiles vim-minimal sssd-client e2fsprogs yum rhel-release"
    elif os_name == "alpine":
      list = "alpine-base"
    else:
      list = ""

    return list.split()

  def package_list_add(self, os_name, os_version):
    if os_name == "fedora":
      list = "procps-ng"
      list =""
    elif os_name == "centos":
      list = ""
    elif os_name == "rhel":
      list = ""
    else: 
      list = ""

    return list.split()

  def get_repository_list(self, os_name, os_version):

    if os_name == "fedora":
      list = [os_name,"updates"]
    elif os_name == "centos":
      list = [os_name+"-"+"base",os_name +"-" "updates"]
    elif os_name == "alpine":
      list = [ "http://dl-cdn.alpinelinux.org/alpine/v3.5/main" ]
    else:
     list = [] 

    return list

  def mkdir_p(self,path):
#    print(path)
    try:
        os.makedirs(path)
#        print("success")
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

  def execute2(self, cmd, home_dir):
    my_env = os.environ.copy()
    # this setting is importent to get the ".rpmmacro" from a "home" directory of our choice
    my_env["HOME"] = home_dir
    process  = subprocess.Popen(cmd,  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=my_env)

    while True:
      out = process.stdout.readline()
      if out == b'' and process.poll() != None:
        break
      if out != b'':
        print(out.decode('utf-8'), end="")

    return process.returncode


class AlpinePackageManager(PackageManagerBase):
  def __init__(self):
    pass


class RedhatPackageManager(PackageManagerBase):
  def __init__(self):
    self.test = ""
  def install_distribution(self):
    self.test = ""

  def create_package_manager_conf_file(self, package_manager, build_dir, http_proxy='', nodocs=''):
    array=[]
    array.append("[main]")
    array.append("gpgcheck=1")
    array.append("installonly_limit=3")
    array.append("clean_requirements_on_remove=true")
    # cachedir will be used when already running the "chroot" environment
    # thereforee there MUST NOT be a "build_dir" prefix
    array.append("cachedir=/var/cache/"+package_manager+"/$basearch/$releasever")
    array.append("reposdir="+build_dir+"/etc/yum.repos.d")
    array.append("pluginconfpath="+build_dir+"/etc/"+package_manager+"/plugins")
  

    if nodocs == 1:
      array.append("tsflags=nodocs")

    if len(http_proxy) > 0:
      array.append("proxy="+http_proxy)
          
    array.append('')

    result = "\n".join(array)
    return result

  def create_nodocs_plugin(self, target_lang, package_manager):
    array=[]
    array.append("[main]")
    array.append("# all installed "+package_manager+" plugins are enabled by default")
    array.append("# to disable this plugin use \"--disableplugin=langpacks\" to "+package_manager+" command.") 
    array.append("")
    array.append("# langpacks plugin is used when any of following is available:")
    array.append("# - any previously installed langpacks (stored in /var/lib/dnf/plugins/installed_langpacks)")
    array.append("# - any languages specified by $LANGUAGE")
    array.append("# - any langpacks listed in langpack_locales below")
    array.append("# -- if this variable is empty, the value of $LANG is considered")
    array.append("")
    array.append("#langpack_locales = ja, zh_CN, cs, pt_BR, mr")
    array.append("# Added by Anaconda")
    array.append("langpack_locales="+target_lang)
    array.append("enabled=1")
    array.append('')
    result = "\n".join(array)
#    print(result)
    return result

  def rpm_target_lang(self, target_lang):

    if isinstance(target_lang, list): 
      new_list=[]
      for item in target_lang:
         new_list.append(item.replace('.UTF-8','.utf8'))
      target_lang=':'.join(new_list)
      #print(target_lang) 
    else: 
      target_lang = target_lang.replace('.UTF-8','.utf8')

    array=[]
    array.append('#       A colon separated list of desired locales to be installed;')
    array.append('#       "all" means install all locale specific files.')
    array.append('#       Example: %_install_langs cs_CZ.utf8:cs_CZ:cs:en_US.utf8:en_US:en')
    array.append('')
    array.append("%_install_langs\t"+target_lang)
    array.append('')
    result = "\n".join(array)
    #print(result)
    #sys.exit(0)
    return result
 

  def install_distribution(self, package_manager, target_os_version, install_root, repo_list, package_list, build_dir):
    self.test=""
    array=[]
    array.append(package_manager)
    array.append("-y")
    array.append("-c")
    array.append(build_dir+"/etc/"+package_manager+".conf")
    array.append("--releasever="+str(target_os_version))
    array.append("--nogpg")
    array.append("--installroot="+install_root)
    array.append("--disablerepo=*")
    array.extend(["--enablerepo="+repo for repo in repo_list])
    array.append("install")
    array.extend(package_list)
    return array

  def create_repo_url(self,repo_var,baseurl):
    if baseurl != "":
      return baseurl
    return "metalink=https://mirrors.fedoraproject.org/metalink?repo="+repo_var+"$releasever&arch=$basearch"


  def install_yum_repo(self,repo_short_name, baseurl=""):

    if repo_short_name == "fedora":
        repo_name = "Fedora $releasever - $basearch"
        baseurl   = self.create_repo_url("fedora-", baseurl)

    if repo_short_name == "updates":
        repo_name = "Fedora $releasever - $basearch - Updates"
        baseurl   = self.create_repo_url("updates-released-f", baseurl)

    if repo_short_name == "updates-testing":
        repo_name = "Fedora $releasever - $basearch - Test Updates"
        baseurl   = self.create_repo_url("updates-testing-f",baseurl)

    array=[]
    array.append("["+repo_short_name+"]")
    array.append("name="+repo_name)
    array.append("failovermethod=priority")
    array.append(baseurl)
    array.append("enabled=1")
    array.append("metadata_expire=1h")
    array.append("gpgcheck=1")
    array.append("gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-$releasever-$basearch")
    array.append("skip_if_unavailable=False")
    result = "\n".join(array)
    return result


  def install_yum_repo_centos(self):
    result = """
[centos-base]
name=CentOS-$releasever - Base
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=os&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/os/$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7
enabled=0

#released updates
[centos-updates]
name=CentOS-$releasever - Updates
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=updates&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/updates/$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7
enabled=0

#additional packages that may be useful
[centos-extras]
name=CentOS-$releasever - Extras
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=extras&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/extras/$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7
enabled=0

#additional packages that extend functionality of existing packages
[centos-centosplus]
name=CentOS-$releasever - Plus
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=centosplus&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/centosplus/$basearch/
gpgcheck=1
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7
"""
    return result

  def execute(self, cmd):
#    print("HERE!")
#    print(cmd)
    process  = subprocess.Popen(cmd,  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:
      out = process.stdout.readline()
      if out == b'' and process.poll() != None:
        break
      if out != b'':
        print(out.decode('utf-8'), end="")


  def dump(self, host, target):
    print("HOST_OS_NAME      : "+ host.os_name)
    print("HOST_OS_VERSION   : "+ host.os_version)
    print("HOST_LANG         : "+ host.lang)
    print("PACKAGE_MANAGER   : "+ host.package_manager)
    print("")
    print("PROFILE           : "+ target.profile)
    print("TARGET_OS_NAME    : "+ target.os_name)
    print("TARGET_OS_VERSION : "+ target.os_version)
    print("TARGET_LANG       : "+ target.lang)
    print("TARGET_LANG_ALL   : "+ target.lang_all)
    print("TARGET_NODOCS     : "+ target.nodocs)
    print("")
    print("REPO_LIST         : "+ " ".join(target.repo_list))
    print("PACKAGE_LIST      : "+ " ".join(target.package_list))
    print("PACKAGE_LIST_ADD  : "+ " ".join(target.package_list_add))
    print("PACKAGE_MANAGER   : "+ target.package_manager)
    print("")
    print("IMAGE_NAME        : "+target.image_name)
    print("")
    print("WORK_DIR          : "+target.work_dir)
    print("BUILD_DIR         : "+target.build_dir)
    print("INSTALL_ROOT      : "+target.install_root)


  def current_dir(self):
    return os.getcwd() 

  def tofile(self, content, filename):
    with open(filename, "w") as f:
      f.write(content)

  def copy(self, wildcard, dest_dir):
#    print(wildcard)
    for file in glob.glob(wildcard):
#      print("File: "+file)
      shutil.copy(file, dest_dir)


def merge_recursive(target, source):
  for key in source:
    value = source[key]
    # Dictionaries in dictionaries need special treatment
    if key in target and isinstance(value, dict):
      tmp_target = target[key]
      merge_recursive(tmp_target,value)
      target[key] = tmp_target
    else:
      target[key]  = value


def merge_config(filename, configuration): 
  if os.path.exists(filename):
    f = open(filename, 'r')
    y = yaml.load(f)
    f.close()
    merge_recursive(configuration, y)

class Patch:
  def __init__(self):
    pass 

  def apply(self, target_lang, target_package_manager, install_dir, nodocs, proxy_url):
    self.install_dir = install_dir
    self.target_lang = target_lang

    if target_package_manager == "dnf":
      self.dnf_conf(nodocs,proxy_url)
    elif target_package_manager == "yum":
      self.yum_conf(nodocs,proxy_url)

    content = self.locale_content()
#    print(content)
    content = self.adjtime_content()
#    print(content)
    self.locale_conf()
    self.adjtime()
    self.clean(install_dir, target_package_manager)

  def locale_conf(self, filename="/etc/locale.conf"):
    print("Patching /etc/locale.conf")
    content = self.locale_content()
    self.tofile(content, self.install_dir + filename)

  def adjtime(self, filename="/etc/adjtime"):
    print("Patching /etc/adjtime")
    content = self.adjtime_content()
    self.tofile(content, self.install_dir + filename)

  def dnf_conf(self, nodocs, proxy, filename="etc/dnf/dnf.conf"):
    print("Patching /etc/dnf/dnf.conf")
    configParser = configparser.ConfigParser()
    fullpath     = os.path.join(self.install_dir, filename)
    configParser.read(fullpath)

    if nodocs == 1:
      configParser.set('main', 'tsflags', 'nodocs')
    if len(proxy) > 0:
      configParser.set('main', 'proxy', proxy)

    out = open(fullpath, 'w')
    configParser.write(out, space_around_delimiters=False)
    out.close()

  def yum_conf(self, nodocs, proxy, filename="etc/yum.conf"):
    print("Patching /"+filename)
    configParser = configparser.ConfigParser()
    fullpath     = os.path.join(self.install_dir, filename)
    print(fullpath)
    configParser.read(fullpath)

    if nodocs == 1:
      configParser.set('main', 'tsflags', 'nodocs')
    if len(proxy) > 0:
      configParser.set('main', 'proxy', proxy)

    out = open(fullpath, 'w')
    configParser.write(out, space_around_delimiters=False)
    out.close()



 
  def tofile(self, content, filename):
    with open(filename, "w") as f:
      f.write(content)

  def locale_content(self):
    if isinstance(self.target_lang, list):
      # Policy: Pick first language
      return "LANG=\""+self.target_lang[0]+"\"\n"
    else: 
      return "LANG=\""+self.target_lang+"\"\n"

  def adjtime_content(self):
    return "0.0 0 0.0\n0\nUTC\n"

  def clean(self,install_root, package_manager):
    self.test=""

    array = ['find', install_root+'/var/lib/'+package_manager+'/history', '-type' , 'f', '-exec', 'rm', '{}', ';']
    print(array)
    subprocess.call(array)

    array = ['find', install_root+'/var/lib/'+package_manager+'/yumdb', '-mindepth','2', '-maxdepth','2',  '-type' , 'd', '-exec', 'rm', '-rf', '{}', ';']
    print(array)
    subprocess.call(array)

 
    array = ['find', install_root+'/var/cache/'+package_manager, '-type' , 'f', '-exec', 'rm', '{}', ';']
    print(array)
    subprocess.call(array)


    log_dir_wildcard = install_root+"/var/log/"+package_manager+"*.log"
    for file in glob.glob(log_dir_wildcard):
      print(file)
      os.remove(file) 
    log_dir_wildcard = install_root+"/var/log/hawkey.log"
    for file in glob.glob(log_dir_wildcard):
      print(file)
      os.remove(file) 
    log_dir_wildcard = install_root+"/var/log/lastlog"
    for file in glob.glob(log_dir_wildcard):
      print(file)
      os.remove(file) 
    subprocess.call(['touch', log_dir_wildcard])


class Installer:
#  def  __init__(self, default_configuration):
#    pass

  def prepare_redhat_distribution(self,configuration, work,target,os_name,os_version):
    rpm = RedhatPackageManager()

    yum_repos_dir  = os.path.join(work.build_dir, "etc", "yum.repos.d")
    repo_conf_file = os.path.join(work.build_dir, "etc", target.package_manager+".conf")
    home_dir       = os.path.join(work.build_dir, "root")
    rpm_build_file = os.path.join(home_dir, ".rpmmacros")
    rpm_dir        = os.path.join(work.install_dir, "etc", "rpm")
    rpm_conf_file  = os.path.join(work.install_dir, "etc", "rpm", "image-language.conf")


    for dir in [ work.install_dir, yum_repos_dir, home_dir, rpm_dir]:
      print(dir)
      rpm.mkdir_p(dir)

    print(repo_conf_file)
    print(rpm_build_file)
    print(rpm_conf_file)

    #rpm.mkdir_p(yum_repos_dir)
    # FIXME need to create all of the configs
    #print(work.http_proxy)
    #sys.exit(0)
    content = rpm.create_package_manager_conf_file(target.package_manager, work.build_dir, work.http_proxy, target.nodocs)
    #print(content)
    #exit(1)
    rpm.tofile(content, repo_conf_file)
    
    repo_url = {}
    if "repo_url" in configuration["target"]:
        repo_url = configuration["target"]["repo_url"]

    if os_name == "fedora":
      for repo_name in target.repo_list:
        url=""
        if repo_name in repo_url:
            url="baseurl="+repo_url[repo_name]
        #print(url)
        content = rpm.install_yum_repo(repo_name, url)
        rpm.tofile(content, os.path.join(yum_repos_dir, repo_name+".repo" ))
 
    elif os_name == "centos":
      content = rpm.install_yum_repo_centos()
      rpm.tofile(content, os.path.join(yum_repos_dir, "fedora-updates-testing.repo"))

    # lang_all = 0 (FALSE) --> install only specific languages
    if target.lang_all == 0:
      rpm.mkdir_p(rpm_dir)
      rpm.mkdir_p(home_dir)

      content = rpm.rpm_target_lang(target.lang)
      rpm.tofile(content, os.path.join(rpm_dir ,"macros.image-language.conf"))
      rpm.tofile(content, os.path.join(home_dir,".rpmmacros"))

    cmd = rpm.install_distribution(
      target.package_manager, 
      target.os_version, 
      work.install_dir,
      target.repo_list,
      target.package_list,
      work.build_dir
    )
    return cmd

  def prepare_alpine_distribution(self, configuration, work, target):
    apm = AlpinePackageManager()
    array = ['apk']
    for repo in target.repo_list:
      array.extend(["--repository", repo])
    array.extend([ '--root', work.install_dir , '--allow-untrusted', '--update-cache' , '--initdb', '--no-progress', 'add', 'alpine-base' ])
    cmd=array
    return cmd

  def main(self, default_configuration, config_file=""):

    configuration         = default_configuration.copy()
    osrelease             = OsRelease()
    locale                = Locale()
    pmb                   = PackageManagerBase()
    package_manager       = pmb.determine_package_manager(osrelease.ID, osrelease.VERSION_ID)

    host_configuration = {
      "host" : {
        "os_name"         : osrelease.ID,
        "os_version"      : osrelease.VERSION_ID,
        "lang"            : locale.LANG,
        "package_manager" : package_manager,
      },
      "target" : {
        "os_name"         : osrelease.ID,
        "os_version"      : osrelease.VERSION_ID,
        "package_manager" : package_manager,
      },
      "work": {
        "build_root": "/var/lib/build",
        "http_proxy"      : '',
      }
    }
    merge_recursive(configuration, host_configuration)
    filename = "image.yaml"

    # Merge configs found in "/etc" local or in "etc", "." relative to the script directory
    for dir_prefix in [ "/etc" , os.path.join(sys.path[0], "etc"), sys.path[0] ]:
      fullpath = os.path.join(dir_prefix, filename)
      merge_config(fullpath, configuration)

    if config_file != "":
      fullpath = os.path.abspath(config_file)
      merge_config(fullpath, configuration)

    target     = configuration['target']
    os_name    = target['os_name'] 
    os_version = target['os_version'] 

    if not 'repo_list' in target:
      target['repo_list'] = pmb.get_repository_list(os_name,os_version)
    if not 'repo_list_add' in target:
       pass  # FIXME
    if not 'package_list' in target:
      target['package_list'] = pmb.package_list(os_name,os_version)
    if not 'package_list_add' in target:
      target['package_list_add'] = pmb.package_list_add(os_name,os_version)

    configuration['target']=target
    
    target = DictToObject(configuration['target'])
    work                 = configuration['work']
    work['build_dir']    = os.path.join(configuration['work']['build_root'], target.os_name +"-" + str(target.os_version), target.profile)
    work['install_dir']  = os.path.join(work['build_dir'],"install")

    configuration['work']= work

    if "docker" in configuration:
      image_name=configuration["docker"]["image"]
      image_name = image_name.replace("%os_name%",    os_name)
      image_name = image_name.replace("%os_version%", str(os_version))
      configuration["docker"]["image"] = image_name

    val=yaml.dump(configuration, explicit_start=True,indent=2, default_flow_style=False)
    print(val)
    work = DictToObject(configuration['work'])
    #sys.exit(0)
  
    pmb.mkdir_p(work.install_dir)

    if os_name == "alpine":
      cmd = self.prepare_alpine_distribution(configuration,work,target)
    else:
      cmd = self.prepare_redhat_distribution(configuration,work,target,os_name,os_version) 

    print(cmd)
    return_code = pmb.execute2(cmd, work.build_dir+"/root") 
    if return_code != 0:
      sys.exit(1)

    Patch().apply(target.lang, target.package_manager,work.install_dir,target.nodocs, target.proxy)

    if os_name == "fedora":
      cmd = [ 'chroot', work.install_dir, 'rpm', '--import', '/etc/pki/rpm-gpg/RPM-GPG-KEY-'+os_name+'-'+str(os_version)+'-primary' ]
      print(" ".join(cmd))
      return_code = pmb.execute2(cmd, "/root")
      print(return_code)

    if "docker" in configuration:
      image_name=configuration["docker"]["image"]
      print("Creating image: "+image_name)
      a="cd \"" + work.install_dir + "\" && tar -c . |docker import - \""+image_name+"\""
      subprocess.call(a,  shell=True)



default_configuration = {
  "version":  "1.0",
  "target": {
    "lang":     'en_US.UTF-8',
    "lang_all": 0,
    "nodocs":   1,
    "profile":  "default",
    "lang":     "en_US.UTF-8",
    "lang_all":  0,
    "profile":   'full',
    "proxy": "",
  }
}

if __name__ == "__main__":
  if os.geteuid() != 0:
    exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")

  install=Installer()
  #if len(sys.argv) < 2:
  #  print(sys.argv[0] + " [config_file]")
  #  sys.exit(1)
  if len(sys.argv) < 2:
    install.main(default_configuration, "")
  else:
    install.main(default_configuration, sys.argv[1])

