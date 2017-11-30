// This file implements the INamedPropertyStore Interface and Gateway for Python.
// Generated by makegw.py

#include "PythonCOM.h"
#include "PythonCOMServer.h"
#include "propsys.h"
#include "PyINamedPropertyStore.h"
#include "PyPROPVARIANT.h"

// @doc - This file contains autoduck documentation
// ---------------------------------------------------
//
// Interface Implementation

PyINamedPropertyStore::PyINamedPropertyStore(IUnknown *pdisp):
	PyIUnknown(pdisp)
{
	ob_type = &type;
}

PyINamedPropertyStore::~PyINamedPropertyStore()
{
}

/* static */ INamedPropertyStore *PyINamedPropertyStore::GetI(PyObject *self)
{
	return (INamedPropertyStore *)PyIUnknown::GetI(self);
}

// @pymethod <o PyPROPVARIANT>|PyINamedPropertyStore|GetNamedValue|Retrieves a property value by name
PyObject *PyINamedPropertyStore::GetNamedValue(PyObject *self, PyObject *args)
{
	INamedPropertyStore *pINPS = GetI(self);
	if ( pINPS == NULL )
		return NULL;
	TmpWCHAR name;
	PROPVARIANT val;
	PyObject *obname;
	// @pyparm str|Name||Name of the property
	if (!PyArg_ParseTuple(args, "O:GetNamedValue", &obname))
		return NULL;
	if (!PyWinObject_AsWCHAR(obname, &name, FALSE))
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pINPS->GetNamedValue(name, &val);
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pINPS, IID_INamedPropertyStore );
	return PyWinObject_FromPROPVARIANT(&val);
}

// @pymethod |PyINamedPropertyStore|SetNamedValue|Sets the value of a property
PyObject *PyINamedPropertyStore::SetNamedValue(PyObject *self, PyObject *args)
{
	INamedPropertyStore *pINPS = GetI(self);
	if ( pINPS == NULL )
		return NULL;
	TmpWCHAR name;
	PyObject *obname, *obval;
	PROPVARIANT *pval;
	// @pyparm <o Py__RPC__in REFPROPVARIANT>|propvar||Description for propvar
	if ( !PyArg_ParseTuple(args, "OO:SetNamedValue", &obname, &obval))
		return NULL;
	if (!PyWinObject_AsWCHAR(obname, &name, FALSE))
		return NULL;
	if (!PyWinObject_AsPROPVARIANT(obval, &pval))
		return NULL;

	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pINPS->SetNamedValue(name, *pval);
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pINPS, IID_INamedPropertyStore );
	Py_INCREF(Py_None);
	return Py_None;

}

// @pymethod int|PyINamedPropertyStore|GetNameCount|Retrieves the number of named properties in the store
PyObject *PyINamedPropertyStore::GetNameCount(PyObject *self, PyObject *args)
{
	INamedPropertyStore *pINPS = GetI(self);
	if ( pINPS == NULL )
		return NULL;
	DWORD count;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pINPS->GetNameCount(&count);
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pINPS, IID_INamedPropertyStore );
	return PyLong_FromUnsignedLong(count);
}

// @pymethod str|PyINamedPropertyStore|GetNameAt|Retrieves a property name by zero-based index
PyObject *PyINamedPropertyStore::GetNameAt(PyObject *self, PyObject *args)
{
	INamedPropertyStore *pINPS = GetI(self);
	if ( pINPS == NULL )
		return NULL;
	BSTR name;
	// @pyparm int|Index||Index of the property name
	DWORD i;
	if (!PyArg_ParseTuple(args, "k:GetNameAt", &i))
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pINPS->GetNameAt( i, &name);
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pINPS, IID_INamedPropertyStore );
	return PyWinObject_FromBstr(name, TRUE);
}

// @object PyINamedPropertyStore|Contains a collection of properties indentified by name
static struct PyMethodDef PyINamedPropertyStore_methods[] =
{
	{ "GetNamedValue", PyINamedPropertyStore::GetNamedValue, 1 }, // @pymeth GetNamedValue|Retrieves a property value by name
	{ "SetNamedValue", PyINamedPropertyStore::SetNamedValue, 1 }, // @pymeth SetNamedValue|Sets the value of a property
	{ "GetNameCount", PyINamedPropertyStore::GetNameCount, METH_NOARGS }, // @pymeth GetNameCount|Retrieves the number of named properties in the store
	{ "GetNameAt", PyINamedPropertyStore::GetNameAt, 1 }, // @pymeth GetNameAt|Retrieves a property name by zero-based index
	{ NULL }
};

PyComTypeObject PyINamedPropertyStore::type("PyINamedPropertyStore",
		&PyIUnknown::type,
		sizeof(PyINamedPropertyStore),
		PyINamedPropertyStore_methods,
		GET_PYCOM_CTOR(PyINamedPropertyStore));
// ---------------------------------------------------
//
// Gateway Implementation
STDMETHODIMP PyGNamedPropertyStore::GetNamedValue(
	LPCWSTR pszName,
	PROPVARIANT * ppropvar)
{
	PY_GATEWAY_METHOD;
	PyObject *obname = PyWinObject_FromWCHAR(pszName);
	if (obname==NULL) return MAKE_PYCOM_GATEWAY_FAILURE_CODE("GetNamedValue");
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("GetNamedValue", &result, "O", obname);
	Py_DECREF(obname);
	if (FAILED(hr)) return hr;
	// Caller assumes ownership of the value, so make a copy
	PROPVARIANT *pypv;
	if (!PyWinObject_AsPROPVARIANT(result, &pypv))
		hr = MAKE_PYCOM_GATEWAY_FAILURE_CODE("GetNamedValue");
	else
		hr = PropVariantCopy(ppropvar, pypv);
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGNamedPropertyStore::SetNamedValue(
	LPCWSTR pszName,
	REFPROPVARIANT propvar)
{
	PY_GATEWAY_METHOD;
	PyObject *obname = PyWinObject_FromWCHAR(pszName);
	if (obname==NULL)
		return MAKE_PYCOM_GATEWAY_FAILURE_CODE("SetNamedValue");
	PyObject *obval = PyWinObject_FromPROPVARIANT(propvar);
	if (obval==NULL){
		Py_DECREF(obname);
		return MAKE_PYCOM_GATEWAY_FAILURE_CODE("SetNamedValue");
		}
	HRESULT hr=InvokeViaPolicy("SetNamedValue", NULL, "OO", obname, obval);
	Py_DECREF(obname);
	Py_DECREF(obval);
	return hr;
}

STDMETHODIMP PyGNamedPropertyStore::GetNameCount(
	DWORD * pdwCount)
{
	PY_GATEWAY_METHOD;
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("GetNameCount", &result);
	if (FAILED(hr)) return hr;
	*pdwCount = PyLong_AsUnsignedLong(result);
	if (*pdwCount == (DWORD)-1 &&PyErr_Occurred())
		hr = MAKE_PYCOM_GATEWAY_FAILURE_CODE("GetNamedCount");
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGNamedPropertyStore::GetNameAt(
	DWORD iProp,
	BSTR * pbstrName)
{
	PY_GATEWAY_METHOD;
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("GetNameAt", &result, "k", iProp);
	if (FAILED(hr)) return hr;
	if (!PyWinObject_AsBstr(result, pbstrName, FALSE))
		hr = MAKE_PYCOM_GATEWAY_FAILURE_CODE("GetNamedAt");
	Py_DECREF(result);
	return hr;
}

