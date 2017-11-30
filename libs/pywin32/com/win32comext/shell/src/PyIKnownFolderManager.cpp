// This file implements the IKnownFolderManager Interface for Python.
// Generated by makegw.py

#include "shell_pch.h"
#include "PyIKnownFolderManager.h"

// @doc - This file contains autoduck documentation
// ---------------------------------------------------
//
// Interface Implementation

PyIKnownFolderManager::PyIKnownFolderManager(IUnknown *pdisp):
	PyIUnknown(pdisp)
{
	ob_type = &type;
}

PyIKnownFolderManager::~PyIKnownFolderManager()
{
}

/* static */ IKnownFolderManager *PyIKnownFolderManager::GetI(PyObject *self)
{
	return (IKnownFolderManager *)PyIUnknown::GetI(self);
}

// @pymethod <o PyIID>|PyIKnownFolderManager|FolderIdFromCsidl|Returns the folder id that corresponds to a CSIDL
PyObject *PyIKnownFolderManager::FolderIdFromCsidl(PyObject *self, PyObject *args)
{
	IKnownFolderManager *pIKFM = GetI(self);
	if ( pIKFM == NULL )
		return NULL;
	// @pyparm int|Csidl||The legacy CSIDL identifying a folder
	int csidl;
	IID kfid;
	if ( !PyArg_ParseTuple(args, "i:FolderIdFromCsidl", &csidl))
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIKFM->FolderIdFromCsidl( csidl, &kfid );
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pIKFM, IID_IKnownFolderManager );
	return PyWinObject_FromIID(kfid);
}

// @pymethod int|PyIKnownFolderManager|FolderIdToCsidl|Returns the CSIDL equivalent of a known folder
PyObject *PyIKnownFolderManager::FolderIdToCsidl(PyObject *self, PyObject *args)
{
	IKnownFolderManager *pIKFM = GetI(self);
	if ( pIKFM == NULL )
		return NULL;
	IID kfid;
	// @pyparm <o PyIID>|id||A known folder id (shell.FOLDERID_*)
	int csidl;
	if ( !PyArg_ParseTuple(args, "O&:FolderIdToCsidl", PyWinObject_AsIID, &kfid))
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIKFM->FolderIdToCsidl( kfid, &csidl );
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pIKFM, IID_IKnownFolderManager );
	return PyInt_FromLong(csidl);
}

// @pymethod (<o PyIID>,...)|PyIKnownFolderManager|GetFolderIds|Retrieves all known folder ids.
PyObject *PyIKnownFolderManager::GetFolderIds(PyObject *self, PyObject *args)
{
	IKnownFolderManager *pIKFM = GetI(self);
	if ( pIKFM == NULL )
		return NULL;
	UINT count = 0;
	IID *kfids;
	if ( !PyArg_ParseTuple(args, ":GetFolderIds"))
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIKFM->GetFolderIds(&kfids, &count);
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pIKFM, IID_IKnownFolderManager );
	PyObject *ret = PyTuple_New(count);
	if (ret){
		for (UINT i=0; i<count; i++){
			PyObject *pyiid = PyWinObject_FromIID(kfids[i]);
			if (pyiid == NULL){
				Py_DECREF(ret);
				ret = NULL;
				break;
				}
			PyTuple_SET_ITEM(ret, i, pyiid);
			}
		}
	CoTaskMemFree(kfids);
	return ret;
}

// @pymethod <o PyIKnownFolder>|PyIKnownFolderManager|GetFolder|Returns a folder by its id.
PyObject *PyIKnownFolderManager::GetFolder(PyObject *self, PyObject *args)
{
	IKnownFolderManager *pIKFM = GetI(self);
	if ( pIKFM == NULL )
		return NULL;
	IID kfid;
	IKnownFolder *ret;
	// @pyparm <o PyIID>|id||A known folder id (shell.FOLDERID_*)
	if ( !PyArg_ParseTuple(args, "O&:GetFolder", PyWinObject_AsIID, &kfid))
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIKFM->GetFolder(kfid, &ret);
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pIKFM, IID_IKnownFolderManager );
	return PyCom_PyObjectFromIUnknown(ret, IID_IKnownFolder, FALSE);
}

// @pymethod <o PyIKnownFolder>|PyIKnownFolderManager|GetFolderByName|Returns a folder by canonical name
PyObject *PyIKnownFolderManager::GetFolderByName(PyObject *self, PyObject *args)
{
	IKnownFolderManager *pIKFM = GetI(self);
	if ( pIKFM == NULL )
		return NULL;
	// @pyparm str|Name||The nonlocalized name of a known folder
	PyObject *obname;
	TmpWCHAR name;
	IKnownFolder *ret;
	if ( !PyArg_ParseTuple(args, "O:GetFolderByName", &obname))
		return NULL;
	if (!PyWinObject_AsWCHAR(obname, &name, FALSE))
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIKFM->GetFolderByName(name, &ret);
	PY_INTERFACE_POSTCALL;
	return PyCom_PyObjectFromIUnknown(ret, IID_IKnownFolder, FALSE);
}

BOOL PyWinObject_AsKNOWNFOLDER_DEFINITION(PyObject *obdef, KNOWNFOLDER_DEFINITION& def)
{
	static char *keywords[] = {"Category", "Name", "Description", "Parent",
		"RelativePath", "ParsingName", "Tooltip", "LocalizedName", "Icon",
		"Security", "Attributes", "Flags", "Type", NULL};
	ZeroMemory(&def, sizeof(def));
	if (!PyDict_Check(obdef)){
		PyErr_SetString(PyExc_TypeError, "KNOWNFOLDER_DEFINITION requires a dict");
		return FALSE;
		}
	TmpPyObject obdummy = PyTuple_New(0);
	if (obdummy == NULL)
		return FALSE;
	PyObject *obName, *obDescription, *obRelativePath,
		*obParsingName, *obTooltip, *obLocalizedName, *obIcon, *obSecurity;
	if (!PyArg_ParseTupleAndKeywords(obdummy, obdef, "iOOO&OOOOOOkiO&", keywords,
		&def.category,
		&obName,
		&obDescription,
		PyWinObject_AsIID, &def.fidParent,
		&obRelativePath, &obParsingName, &obTooltip,
		&obLocalizedName, &obIcon, &obSecurity,
		&def.dwAttributes, &def.kfdFlags,
		PyWinObject_AsIID, &def.ftidType))
		return FALSE;
	BOOL ret = PyWinObject_AsTaskAllocatedWCHAR(obName, &def.pszName, FALSE)
			&& PyWinObject_AsTaskAllocatedWCHAR(obDescription, &def.pszDescription, FALSE)
			&& PyWinObject_AsTaskAllocatedWCHAR(obRelativePath, &def.pszRelativePath, TRUE)
			&& PyWinObject_AsTaskAllocatedWCHAR(obParsingName, &def.pszParsingName, TRUE)
			&& PyWinObject_AsTaskAllocatedWCHAR(obTooltip, &def.pszTooltip, TRUE)
			&& PyWinObject_AsTaskAllocatedWCHAR(obLocalizedName, &def.pszLocalizedName, TRUE)
			&& PyWinObject_AsTaskAllocatedWCHAR(obIcon, &def.pszIcon, TRUE)
			&& PyWinObject_AsTaskAllocatedWCHAR(obSecurity, &def.pszSecurity, TRUE);
	if (!ret)
		FreeKnownFolderDefinitionFields(&def);
	return ret;
}

// @pymethod |PyIKnownFolderManager|RegisterFolder|Defines a new known folder
PyObject *PyIKnownFolderManager::RegisterFolder(PyObject *self, PyObject *args)
{
	IKnownFolderManager *pIKFM = GetI(self);
	if ( pIKFM == NULL )
		return NULL;
	IID kfid;
	PyObject *obdef;
	// @pyparm <o PyIID>|id||GUID used to identify the new known folder
	// @pyparm dict|Definition||Dictionary containing info to be placed in a KNOWNFOLDER_DEFINITION struct
	// @comm <om PyIKnownFolder.GetFolderDefinition> can be used to get a template dictionary
	KNOWNFOLDER_DEFINITION def;
	ZeroMemory(&def, sizeof(def));
	if ( !PyArg_ParseTuple(args, "O&O:RegisterFolder", PyWinObject_AsIID, &kfid, &obdef))
		return NULL;
	if (!PyWinObject_AsKNOWNFOLDER_DEFINITION(obdef, def))
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIKFM->RegisterFolder(kfid, &def);
	PY_INTERFACE_POSTCALL;
	FreeKnownFolderDefinitionFields(&def);
	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pIKFM, IID_IKnownFolderManager);
	Py_INCREF(Py_None);
	return Py_None;
}

// @pymethod |PyIKnownFolderManager|UnregisterFolder|Removes the definition of a known folder
PyObject *PyIKnownFolderManager::UnregisterFolder(PyObject *self, PyObject *args)
{
	IKnownFolderManager *pIKFM = GetI(self);
	if ( pIKFM == NULL )
		return NULL;
	IID kfid;
	// @pyparm <o PyIID>|id||GUID of a known folder to be unregistered
	if ( !PyArg_ParseTuple(args, "O&:UnregisterFolder", PyWinObject_AsIID, &kfid))
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIKFM->UnregisterFolder(kfid);
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pIKFM, IID_IKnownFolderManager );
	Py_INCREF(Py_None);
	return Py_None;
}

// @pymethod <o PyIKnownFolder>|PyIKnownFolderManager|FindFolderFromPath|Retrieves a known folder by path
PyObject *PyIKnownFolderManager::FindFolderFromPath(PyObject *self, PyObject *args)
{
	IKnownFolderManager *pIKFM = GetI(self);
	if ( pIKFM == NULL )
		return NULL;
	// @pyparm str|Path||Path of a folder
	// @pyparm int|Mode||FFFP_EXACTMATCH or FFFP_NEARESTPARENTMATCH	
	TmpWCHAR path;
	PyObject *obpath;
	FFFP_MODE mode;
	IKnownFolder *ret;
	if ( !PyArg_ParseTuple(args, "Oi:FindFolderFromPath", &obpath, &mode))
		return NULL;
	if (!PyWinObject_AsWCHAR(obpath, &path, FALSE))
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIKFM->FindFolderFromPath(path, mode, &ret);
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pIKFM, IID_IKnownFolderManager );
	return PyCom_PyObjectFromIUnknown(ret, IID_IKnownFolder, FALSE);
}

// @pymethod <o PyIKnownFolder>|PyIKnownFolderManager|FindFolderFromIDList|Retrieves a known folder using its item id list.
PyObject *PyIKnownFolderManager::FindFolderFromIDList(PyObject *self, PyObject *args)
{
	IKnownFolderManager *pIKFM = GetI(self);
	if ( pIKFM == NULL )
		return NULL;
	IKnownFolder *ret;
	PIDLIST_ABSOLUTE pidl;
	PyObject *obpidl;
	// @pyparm <o PyIDL>|pidl||Item id list of the folder
	if ( !PyArg_ParseTuple(args, "O:FindFolderFromIDList", &obpidl))
		return NULL;
	if (!PyObject_AsPIDL(obpidl, &pidl, FALSE))
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIKFM->FindFolderFromIDList(pidl, &ret);
	PY_INTERFACE_POSTCALL;
	PyObject_FreePIDL(pidl);
	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pIKFM, IID_IKnownFolderManager );
	return PyCom_PyObjectFromIUnknown(ret, IID_IKnownFolder, FALSE);
}

// @pymethod |PyIKnownFolderManager|Redirect|Redirects a known folder to an alternate location
PyObject *PyIKnownFolderManager::Redirect(PyObject *self, PyObject *args)
{
	IKnownFolderManager *pIKFM = GetI(self);
	if ( pIKFM == NULL )
		return NULL;
	IID kfid;
	// @pyparm <o PyIID>|id||Id of the known folder to be redirected
	HWND hwnd;
	// @pyparm <o PyHANDLE>|hwnd||Handle of window to be used for user interaction
	KF_REDIRECT_FLAGS flags;
	// @pyparm int|flags||Combination of KF_REDIRECT_* flags
	TmpWCHAR TargetPath;
	PyObject *obTargetPath;
	// @pyparm str|TargetPath||Path to which the known folder will be redirected
	ULONG cExcludes;
	IID *Excludes = NULL;
	PyObject *obExcludes;
	// @pyparm (<o PyIID>,...)|Exclusion||Sequence of known folder ids of subfolders to be excluded from redirection
	WCHAR *Error = NULL;
	if ( !PyArg_ParseTuple(args, "O&O&iOO:Redirect",
		PyWinObject_AsIID, &kfid,
		PyWinObject_AsHANDLE, &hwnd,
		&flags, &obTargetPath, &obExcludes))
		return NULL;
	if (!PyWinObject_AsWCHAR(obTargetPath, &TargetPath, FALSE))
		return NULL;
	if (!SeqToVector(obExcludes, &Excludes, &cExcludes, PyWinObject_AsIID))
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIKFM->Redirect( kfid, hwnd, flags, TargetPath, cExcludes, Excludes, &Error);
	PY_INTERFACE_POSTCALL;
	CoTaskMemFree(Excludes);
	if ( FAILED(hr) ){
		// ??? Need to figure out how to return Error string with exception ???
		PyCom_BuildPyException(hr, pIKFM, IID_IKnownFolderManager );
		CoTaskMemFree(Error);
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

// @object PyIKnownFolderManager|Interface used to manage known folder definitions.
static struct PyMethodDef PyIKnownFolderManager_methods[] =
{
	{ "FolderIdFromCsidl", PyIKnownFolderManager::FolderIdFromCsidl, 1 }, // @pymeth FolderIdFromCsidl|Returns the folder id that corresponds to a CSIDL
	{ "FolderIdToCsidl", PyIKnownFolderManager::FolderIdToCsidl, 1 }, // @pymeth FolderIdToCsidl|Returns the CSIDL equivalent of a known folder
	{ "GetFolderIds", PyIKnownFolderManager::GetFolderIds, 1 }, // @pymeth GetFolderIds|Retrieves all known folder ids.
	{ "GetFolder", PyIKnownFolderManager::GetFolder, 1 }, // @pymeth GetFolder|Returns a folder by its id
	{ "GetFolderByName", PyIKnownFolderManager::GetFolderByName, 1 }, // @pymeth GetFolderByName|Returns a folder by its canonical name
	{ "RegisterFolder", PyIKnownFolderManager::RegisterFolder, 1 }, // @pymeth RegisterFolder|Defines a new known folder
	{ "UnregisterFolder", PyIKnownFolderManager::UnregisterFolder, 1 }, // @pymeth UnregisterFolder|Removes the definition of a known folder
	{ "FindFolderFromPath", PyIKnownFolderManager::FindFolderFromPath, 1 }, // @pymeth FindFolderFromPath|Retrieves a known folder by path
	{ "FindFolderFromIDList", PyIKnownFolderManager::FindFolderFromIDList, 1 }, // @pymeth FindFolderFromIDList|Retrieves a known folder using its item id list.
	{ "Redirect", PyIKnownFolderManager::Redirect, 1 }, // @pymeth Redirect|Redirects a known folder to an alternate location
	{ NULL }
};

PyComTypeObject PyIKnownFolderManager::type("PyIKnownFolderManager",
		&PyIUnknown::type,
		sizeof(PyIKnownFolderManager),
		PyIKnownFolderManager_methods,
		GET_PYCOM_CTOR(PyIKnownFolderManager));
