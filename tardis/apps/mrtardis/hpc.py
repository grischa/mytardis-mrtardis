# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__ = "grischa"
__date__ = "$17/09/2010 3:02:10 PM$"

from tardis.tardis_portal.logger import logger


if __name__ == "__main__":
    print "Hello World"

# IMPORTS
import paramiko
import StringIO
import stat


class hpc:
    types = ("sge", "pbs")
    queuetype = None
    hostname = None
    username = None
    privateKey = None
    authtype = "key"
    client = None
    sftpclient = None

    def __init__(self, hostname, username, queuetype="sge", authtype="key",
                 key=None, keytype=None):
        self.queuetype = queuetype
        self.hostname = hostname
        self.username = username
        self.authtype = authtype
        if authtype == "key":
            self.setKey(key, keytype)
        self.client = paramiko.SSHClient()
        policy = paramiko.AutoAddPolicy()
        self.client.set_missing_host_key_policy(policy)
        self.client.connect(hostname=self.hostname, username=self.username,
                            pkey=self.privateKey)

    def __del__(self):
        if self.client != None:
            try:
                self.client.close()
            except:
                pass

    def setKey(self, privateKeyString, keytype):
        privateKeyFileObj = StringIO.StringIO(privateKeyString)
        if keytype == "rsa":
            self.privateKey = paramiko.RSAKey.from_private_key(
                privateKeyFileObj)
        elif keytype == "dss":
            self.privateKey = paramiko.DSSKey.from_private_key(
                privateKeyFileObj)

    def initSFTP(self):
        if self.sftpclient == None:
            self.sftpclient = paramiko.SFTPClient.from_transport(
                self.client.get_transport())

    def upload(self, remoterelativepath, filelist, localpath=""):
        """upload files to hpc using path parameters"""
        self.initSFTP()
        remotepath = "/nfs/monash/home/" + self.username +\
            "/" + remoterelativepath
        self.sftpclient.mkdir(remotepath)
        for filename in filelist:
            localfilepath = localpath + "/" + filename
            remotefilepath = remotepath + "/" + filename
            #print remotefilepath
            self.sftpclient.put(localfilepath, remotefilepath, callback=None)

    def download(self, remotepath, localpath,
                 filelist=None, excludefiles=None):
        self.initSFTP()
        if filelist == None:
            filelist = self.sftpclient.listdir(remotepath)
        filteredlist = []
        if excludefiles != None:
            for filename in filelist:
                if filename not in excludefiles:
                    filteredlist.append(filename)
        else:
            filteredlist = filelist
        for filename in filteredlist:
            localfilepath = localpath + "/" + filename
            remotefilepath = remotepath + "/" + filename
            self.sftpclient.get(remotefilepath, localfilepath)

    def testConnection(self):
        testhost = self.getOutputError("hostname")[0]
        #print testhost
        #print self.hostname
        logger.debug("testing connection in hpc.py")
        if testhost.strip() == self.hostname.strip():
            return True
        else:
            return False

    def getOutputError(self, command):
        stdin, stdout,  stderr = self.client.exec_command(command)
        retout = stdout.read()
        reterr = stderr.read()
        stdin.close()
        stdout.close()
        stderr.close()
        return (retout, reterr)

    def rmtree(self, path):
        self.initSFTP()
        pathstat = self.sftpclient.lstat(path)
        #print path
        if stat.S_ISDIR(pathstat.st_mode):
            filelist = self.sftpclient.listdir(path)
            if len(filelist) > 0:
                for filebasename in filelist:
                    filename = path + "/" + filebasename
                    filestat = self.sftpclient.lstat(filename)
                    if stat.S_ISDIR(filestat.st_mode):
                        self.rmtree(filename)
                    else:
                        self.sftpclient.remove(filename)
            self.sftpclient.rmdir(path)
        else:
            self.sftpclient.remove(path)
