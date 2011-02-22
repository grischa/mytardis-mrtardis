from tardis.apps.mrtardis.models import HPCUser

from tardis.tardis_portal.models import Dataset_File
import tardis.apps.mrtardis.hpc as hpc

import tardis.apps.mrtardis.secrets as secrets
import zipfile
from tardis.tardis_portal.logger import logger


def test_hpc_connection(user):
    """returns True/False after trying to connect to the cluster,
    sets a flag if successful and returns True if flag is set as
    True without testing the connection first"""
    logger.debug("testing if user exists")
    try:
        hpcuser = HPCUser.objects.get(user=user)
    except HPCUser.DoesNotExist:
        return False
    #logger.debug(dir(hpcuser))
    if hpcuser.testedConnection:
        #logger.debug("testConnection = True")
        return hpcuser.hpc_username
    myHPC = hpc.hpc(secrets.hostname,
                    hpcuser.hpc_username,
                    queuetype="sge", authtype="key",
                    key=secrets.privatekey, keytype="rsa")
    if myHPC.testConnection():
        hpcuser.testedConnection = True
        #logger.debug("tested for real: " + repr(hpcuser.testedConnection))
        hpcuser.save()
        return hpcuser.hpc_username
    else:
        hpcuser.testedConnection = False
        hpcuser.save()
        return False


def getPublicKey():
    return secrets.publickey


def extractMetaDataFromMTZFile(filepath):
    """extracts meta data from end of MTZ file"""
    ifile = open(filepath, 'r')
    file_contents = ""
    lines = ifile.readlines()
    for line in lines:
        if "VERS MTZ" in line.upper():
            file_contents += line + "\n"
    ifile.close()
    meta_data_start = file_contents.index("VERS MTZ")
    meta_data = file_contents[meta_data_start:].strip()
    meta = []
    for i in range(len(meta_data) / 80 + 1):
        if (i + 1) * 80 < len(meta_data):
            meta.append(meta_data[i * 80:(i + 1) * 80])
        else:
            meta.append(meta_data[i * 80:])
    return meta


def sgNumNameTrans(number=None, name=None):
    ttable = {1: "P1",
              3: "P2", 4: "P21",
              5: "C2",
              16: "P222", 17: "P2221", 18: "P21212", 19: "P212121",
              20: "C2221", 21: "C222",
              22: "F222",
              23: "I222", 24: "I212121",
              75: "P4", 76: "P41", 77: "P42", 78: "P43",
              79: "I4", 80: "I41",

              89: "P422", 90: "P4212", 91: "P4122", 92: "P41212", 93: "P4222",
              94: "P42212", 95: "P4322", 96: "P43212",

              97: "I422", 98: "I4122",
              143: "P3", 144: "P31", 145: "P32",
              146: "R3", 155: "R32",
              149: "P312", 151: "P3112", 153: "P3212",
              150: "P321", 152: "P3121", 154: "P3221",

              168: "P6", 169: "P61", 170: "P65", 171: "P62",
              172: "P64", 173: "P63",

              177: "P622", 178: "P6122", 179: "P6522", 180: "P6222",
              181: "P6422", 182: "P6322",

              195: "P23", 198: "P213",
              196: "F23",
              197: "I23", 199: "I213",
              207: "P432", 208: "P4232",
              209: "F432", 210: "F4132", 212: "P4332", 213: "P4132",
              211: "I432", 214: "I4132", }
    if number != None and name == None:
        if type(number).__name__ != 'int':
            number = int(number)
        return ttable[number]
    elif number == None and name != None:
        for (key, value) in ttable.iteritems():
            if value == name:
                return key
    else:
        return False
    return False


def getGroupNumbersFromNumber(number):
    """get Space Groups in Group from Space Group number"""
    r = lambda x, y: range(x, y + 1)  # useful shortcut for ranges
    grouping = [[1],  # triclinic
                [3, 4],  # monoclinic p
                [5],  # monoclinic c
                r(16, 19),  # orthorhombic p
                [20, 21],  # orthorhombic c
                [22],  # orthorhombic f
                [23, 24],  # orthorhombic i
                r(75, 78),  # tetragonal p4
                [79, 80],  # tetragonal i4
                r(89, 96),  # tetragonal p422
                [97, 98],  # tetragonal i422
                r(143, 145),  # trigonal p3
                [146, 155],  # trigonal r
                [149, 151, 153],  # trigonal p312
                [150, 152, 154],  # trigonal p321
                r(168, 173),  # hexagonal p6
                r(177, 182),  # hexagonal p622
                [195, 198],  # cubic p2
                [196],  # cubic f2
                [197, 199],  # cubic i2
                [207, 208, 212, 213],  # cubic p4
                [209, 210],  # cubic f4
                [211, 214],  # cubic i4
                ]
    mydict = dict()
    for item in grouping:
        for jtem in item:
            mydict[jtem] = item
    if number in mydict:
        return mydict[number]
    else:
        return []


def calcMW(sequence):
    """input sequence and get molecular weight"""
    MWtable = {"A": 71.0788, "C": 103.1388, "D": 115.0886,
               "E": 129.1155, "F": 147.1766, "G": 57.0519,
               "H": 137.1411, "I": 113.1594, "K": 128.1741,
               "L": 113.1594, "M": 131.1926, "N": 114.1038,
               "P": 97.1167, "Q": 128.1307, "R": 156.1875,
               "S": 87.0782, "T": 101.1051, "V": 99.1326,
               "W": 186.2132, "Y": 163.1760,
               }
    mw = 0
    for aa in sequence:
        mw += MWtable[aa]
    return mw


def get_mtz_file(dataset_id):
    """Returns the first MTZ file it finds in the dataset"""
    mtzquery = Dataset_File.objects.filter(dataset__pk=dataset_id,
                                           filename__iendswith=".mtz")
    if len(mtzquery) > 0:
        return mtzquery[0]
    else:
        return None


def get_pdb_files(dataset_id, storagePaths=False):
    """
    Return list of pdbfiles contained in dataset. Returns pdb filenames
    including the ones in zip files by default.
    If storagePaths = True, return zipfiles unopend if
    they contain pdb files and all files as their full filesystem paths.
    """
    pdbfilenames = []
    zipquery = Dataset_File.objects.filter(dataset__pk=dataset_id,
                                           filename__iendswith=".zip")
    if len(zipquery) > 0:
        for zipfileobj in zipquery:
            zippath = zipfileobj.get_storage_path()
            thiszip = zipfile.ZipFile(zippath, 'r')
            for filename in thiszip.namelist():
                if filename.endswith((".pdb", ".PDB")) and \
                        not filename.startswith("__"):
                    if storagePaths:
                        pdbfilenames.append(zippath)
                        thiszip.close()
                        break
                    else:
                        pdbfilenames.append(filename)
            thiszip.close()
    pdbquery = Dataset_File.objects.filter(dataset__pk=dataset_id,
                                           filename__iendswith=".pdb")
    if len(pdbquery) > 0:
        for pdbfileobj in pdbquery:
            if storagePaths:
                pdbfilenames.append(pdbfileobj.get_storage_path())
            else:
                pdbfilenames.append(pdbfileobj.filename)
    return pdbfilenames


def processMTZ(mtzfile):
    """extract data from metadata block of mtz file"""
    #based on http://www.ccp4.ac.uk/html/mtzformat.html#fileformat
    metadata = extractMetaDataFromMTZFile(mtzfile)
    parameters = dict()
    parameters["f_value"] = []
    parameters["sigf_value"] = []
    for line in metadata:
        first_space = line.find(" ")
        if len(line) > first_space + 1 + 30 + 1 and line[
            first_space + 1 + 30 + 1] == "F":
            parameters["f_value"].append(
                line[7:first_space + 1 + 30 + 1].strip())
        elif len(line) > first_space + 1 + 30 + 1 and line[
            first_space + 1 + 30 + 1] == "Q":
            parameters["sigf_value"].append(
                    line[7:first_space + 1 + 30 + 1].strip())
        elif line.startswith("SYMINF"):
            fields = line.split()
            #print fields[4]
            parameters["spacegroup"] = int(fields[4])
    return parameters
