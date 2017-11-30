// This file implements the IRemoteDebugApplicationThread Interface and Gateway for Python.
// Generated by makegw.py

#include "stdafx.h"
#include "PythonCOM.h"
#include "PythonCOMServer.h"
#include "PyIRemoteDebugApplicationThread.h"

// @doc - This file contains autoduck documentation
// ---------------------------------------------------
//
// Interface Implementation

PyIRemoteDebugApplicationThread::PyIRemoteDebugApplicationThread(IUnknown *pdisp):
	PyIUnknown(pdisp)
{
	ob_type = &type;
}

PyIRemoteDebugApplicationThread::~PyIRemoteDebugApplicationThread()
{
}

/* static */ IRemoteDebugApplicationThread *PyIRemoteDebugApplicationThread::GetI(PyObject *self)
{
	return (IRemoteDebugApplicationThread *)PyIUnknown::GetI(self);
}

// @pymethod |PyIRemoteDebugApplicationThread|GetSystemThreadId|Description of GetSystemThreadId.
PyObject *PyIRemoteDebugApplicationThread::GetSystemThreadId(PyObject *self, PyObject *args)
{
	IRemoteDebugApplicationThread *pIRDAT = GetI(self);
	if ( pIRDAT == NULL )
		return NULL;
	DWORD dwThreadId;
	if ( !PyArg_ParseTuple(args, ":GetSystemThreadId") )
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIRDAT->GetSystemThreadId( &dwThreadId );
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return OleSetOleError(hr);

	PyObject *pyretval = Py_BuildValue("i", dwThreadId);
	return pyretval;
}

// @pymethod |PyIRemoteDebugApplicationThread|GetApplication|Description of GetApplication.
PyObject *PyIRemoteDebugApplicationThread::GetApplication(PyObject *self, PyObject *args)
{
	IRemoteDebugApplicationThread *pIRDAT = GetI(self);
	if ( pIRDAT == NULL )
		return NULL;
	IRemoteDebugApplication * pprda;
	if ( !PyArg_ParseTuple(args, ":GetApplication") )
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIRDAT->GetApplication( &pprda );
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return OleSetOleError(hr);
	PyObject *obpprda;

	obpprda = PyCom_PyObjectFromIUnknown(pprda, IID_IRemoteDebugApplication, FALSE);
	PyObject *pyretval = Py_BuildValue("O", obpprda);
	Py_XDECREF(obpprda);
	return pyretval;
}

// @pymethod |PyIRemoteDebugApplicationThread|EnumStackFrames|Description of EnumStackFrames.
PyObject *PyIRemoteDebugApplicationThread::EnumStackFrames(PyObject *self, PyObject *args)
{
	IRemoteDebugApplicationThread *pIRDAT = GetI(self);
	if ( pIRDAT == NULL )
		return NULL;
	IEnumDebugStackFrames * ppedsf;
	if ( !PyArg_ParseTuple(args, ":EnumStackFrames") )
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIRDAT->EnumStackFrames( &ppedsf );
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return OleSetOleError(hr);
	PyObject *obppedsf;

	obppedsf = PyCom_PyObjectFromIUnknown(ppedsf, IID_IEnumDebugStackFrames, FALSE);
	PyObject *pyretval = Py_BuildValue("O", obppedsf);
	Py_XDECREF(obppedsf);
	return pyretval;
}

// @pymethod |PyIRemoteDebugApplicationThread|GetDescription|Description of GetDescription.
PyObject *PyIRemoteDebugApplicationThread::GetDescription(PyObject *self, PyObject *args)
{
	IRemoteDebugApplicationThread *pIRDAT = GetI(self);
	if ( pIRDAT == NULL )
		return NULL;
	BSTR pbstrDescription;
	BSTR pbstrState;
	if ( !PyArg_ParseTuple(args, ":GetDescription") )
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIRDAT->GetDescription( &pbstrDescription, &pbstrState );
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return OleSetOleError(hr);
	PyObject *obpbstrDescription;
	PyObject *obpbstrState;

	obpbstrDescription = MakeBstrToObj(pbstrDescription);
	obpbstrState = MakeBstrToObj(pbstrState);
	PyObject *pyretval = Py_BuildValue("OO", obpbstrDescription, obpbstrState);
	Py_XDECREF(obpbstrDescription);
	SysFreeString(pbstrDescription);
	Py_XDECREF(obpbstrState);
	SysFreeString(pbstrState);
	return pyretval;
}

// @pymethod |PyIRemoteDebugApplicationThread|SetNextStatement|Description of SetNextStatement.
PyObject *PyIRemoteDebugApplicationThread::SetNextStatement(PyObject *self, PyObject *args)
{
	IRemoteDebugApplicationThread *pIRDAT = GetI(self);
	if ( pIRDAT == NULL )
		return NULL;
	// @pyparm <o PyIDebugStackFrame>|pStackFrame||Description for pStackFrame
	// @pyparm <o PyIDebugCodeContext>|pCodeContext||Description for pCodeContext
	PyObject *obpStackFrame;
	PyObject *obpCodeContext;
	IDebugStackFrame * pStackFrame;
	IDebugCodeContext * pCodeContext;
	if ( !PyArg_ParseTuple(args, "OO:SetNextStatement", &obpStackFrame, &obpCodeContext) )
		return NULL;
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_InterfaceFromPyInstanceOrObject(obpStackFrame, IID_IDebugStackFrame, (void **)&pStackFrame, TRUE /* bNoneOK */))
		 bPythonIsHappy = FALSE;
	if (!PyCom_InterfaceFromPyInstanceOrObject(obpCodeContext, IID_IDebugCodeContext, (void **)&pCodeContext, TRUE /* bNoneOK */))
		 bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIRDAT->SetNextStatement( pStackFrame, pCodeContext );
	if (pStackFrame) pStackFrame->Release();
	if (pCodeContext) pCodeContext->Release();
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;

}

// @pymethod |PyIRemoteDebugApplicationThread|GetState|Description of GetState.
PyObject *PyIRemoteDebugApplicationThread::GetState(PyObject *self, PyObject *args)
{
	IRemoteDebugApplicationThread *pIRDAT = GetI(self);
	if ( pIRDAT == NULL )
		return NULL;
	DWORD pState;
	if ( !PyArg_ParseTuple(args, ":GetState") )
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIRDAT->GetState( &pState );
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return OleSetOleError(hr);

	PyObject *pyretval = Py_BuildValue("i", pState);
	return pyretval;
}

// @pymethod |PyIRemoteDebugApplicationThread|Suspend|Description of Suspend.
PyObject *PyIRemoteDebugApplicationThread::Suspend(PyObject *self, PyObject *args)
{
	IRemoteDebugApplicationThread *pIRDAT = GetI(self);
	if ( pIRDAT == NULL )
		return NULL;
	DWORD pdwCount;
	if ( !PyArg_ParseTuple(args, ":Suspend") )
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIRDAT->Suspend( &pdwCount );
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return OleSetOleError(hr);

	PyObject *pyretval = Py_BuildValue("i", pdwCount);
	return pyretval;
}

// @pymethod |PyIRemoteDebugApplicationThread|Resume|Description of Resume.
PyObject *PyIRemoteDebugApplicationThread::Resume(PyObject *self, PyObject *args)
{
	IRemoteDebugApplicationThread *pIRDAT = GetI(self);
	if ( pIRDAT == NULL )
		return NULL;
	DWORD pdwCount;
	if ( !PyArg_ParseTuple(args, ":Resume") )
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIRDAT->Resume( &pdwCount );
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return OleSetOleError(hr);

	PyObject *pyretval = Py_BuildValue("i", pdwCount);
	return pyretval;
}

// @pymethod |PyIRemoteDebugApplicationThread|GetSuspendCount|Description of GetSuspendCount.
PyObject *PyIRemoteDebugApplicationThread::GetSuspendCount(PyObject *self, PyObject *args)
{
	IRemoteDebugApplicationThread *pIRDAT = GetI(self);
	if ( pIRDAT == NULL )
		return NULL;
	DWORD pdwCount;
	if ( !PyArg_ParseTuple(args, ":GetSuspendCount") )
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIRDAT->GetSuspendCount( &pdwCount );
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return OleSetOleError(hr);

	PyObject *pyretval = Py_BuildValue("i", pdwCount);
	return pyretval;
}

// @object PyIRemoteDebugApplicationThread|Description of the interface
static struct PyMethodDef PyIRemoteDebugApplicationThread_methods[] =
{
	{ "GetSystemThreadId", PyIRemoteDebugApplicationThread::GetSystemThreadId, 1 }, // @pymeth GetSystemThreadId|Description of GetSystemThreadId
	{ "GetApplication", PyIRemoteDebugApplicationThread::GetApplication, 1 }, // @pymeth GetApplication|Description of GetApplication
	{ "EnumStackFrames", PyIRemoteDebugApplicationThread::EnumStackFrames, 1 }, // @pymeth EnumStackFrames|Description of EnumStackFrames
	{ "GetDescription", PyIRemoteDebugApplicationThread::GetDescription, 1 }, // @pymeth GetDescription|Description of GetDescription
	{ "SetNextStatement", PyIRemoteDebugApplicationThread::SetNextStatement, 1 }, // @pymeth SetNextStatement|Description of SetNextStatement
	{ "GetState", PyIRemoteDebugApplicationThread::GetState, 1 }, // @pymeth GetState|Description of GetState
	{ "Suspend", PyIRemoteDebugApplicationThread::Suspend, 1 }, // @pymeth Suspend|Description of Suspend
	{ "Resume", PyIRemoteDebugApplicationThread::Resume, 1 }, // @pymeth Resume|Description of Resume
	{ "GetSuspendCount", PyIRemoteDebugApplicationThread::GetSuspendCount, 1 }, // @pymeth GetSuspendCount|Description of GetSuspendCount
	{ NULL }
};

PyComTypeObject PyIRemoteDebugApplicationThread::type("PyIRemoteDebugApplicationThread",
		&PyIUnknown::type,
		sizeof(PyIRemoteDebugApplicationThread),
		PyIRemoteDebugApplicationThread_methods,
		GET_PYCOM_CTOR(PyIRemoteDebugApplicationThread));
// ---------------------------------------------------
//
// Gateway Implementation

STDMETHODIMP PyGRemoteDebugApplicationThread::GetSystemThreadId(
		/* [out] */ DWORD __RPC_FAR * dwThreadId)
{
	PY_GATEWAY_METHOD;
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("GetSystemThreadId", &result);
	if (FAILED(hr)) return hr;
	// Process the Python results, and convert back to the real params
	if (!PyArg_Parse(result, "i" , dwThreadId)) return PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGRemoteDebugApplicationThread::GetApplication(
		/* [out] */ IRemoteDebugApplication __RPC_FAR *__RPC_FAR * pprda)
{
	PY_GATEWAY_METHOD;
	if (pprda==NULL) return E_POINTER;
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("GetApplication", &result);
	if (FAILED(hr)) return hr;
	// Process the Python results, and convert back to the real params
	PyObject *obpprda;
	if (!PyArg_Parse(result, "O" , &obpprda)) return PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_InterfaceFromPyInstanceOrObject(obpprda, IID_IRemoteDebugApplication, (void **)pprda, TRUE /* bNoneOK */))
		 bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) hr = PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGRemoteDebugApplicationThread::EnumStackFrames(
		/* [out] */ IEnumDebugStackFrames __RPC_FAR *__RPC_FAR * ppedsf)
{
	PY_GATEWAY_METHOD;
	if (ppedsf==NULL) return E_POINTER;
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("EnumStackFrames", &result);
	if (FAILED(hr)) return hr;
	// Process the Python results, and convert back to the real params
	PyObject *obppedsf;
	if (!PyArg_Parse(result, "O" , &obppedsf)) return PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_InterfaceFromPyInstanceOrObject(obppedsf, IID_IEnumDebugStackFrames, (void **)ppedsf, TRUE /* bNoneOK */))
		 bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) hr = PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGRemoteDebugApplicationThread::GetDescription(
		/* [out] */ BSTR __RPC_FAR * pbstrDescription,
		/* [out] */ BSTR __RPC_FAR * pbstrState)
{
	PY_GATEWAY_METHOD;
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("GetDescription", &result);
	if (FAILED(hr)) return hr;
	// Process the Python results, and convert back to the real params
	PyObject *obpbstrDescription;
	PyObject *obpbstrState;
	if (!PyArg_ParseTuple(result, "OO" , &obpbstrDescription, &obpbstrState)) return PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_BstrFromPyObject(obpbstrDescription, pbstrDescription)) bPythonIsHappy = FALSE;
	if (!PyCom_BstrFromPyObject(obpbstrState, pbstrState)) bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) hr = PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGRemoteDebugApplicationThread::SetNextStatement(
		/* [in] */ IDebugStackFrame __RPC_FAR * pStackFrame,
		/* [in] */ IDebugCodeContext __RPC_FAR * pCodeContext)
{
	PY_GATEWAY_METHOD;
	PyObject *obpStackFrame;
	PyObject *obpCodeContext;
	obpStackFrame = PyCom_PyObjectFromIUnknown(pStackFrame, IID_IDebugStackFrame, TRUE);
	obpCodeContext = PyCom_PyObjectFromIUnknown(pCodeContext, IID_IDebugCodeContext, TRUE);
	HRESULT hr=InvokeViaPolicy("SetNextStatement", NULL, "OO", obpStackFrame, obpCodeContext);
	Py_XDECREF(obpStackFrame);
	Py_XDECREF(obpCodeContext);
	return hr;
}

STDMETHODIMP PyGRemoteDebugApplicationThread::GetState(
		/* [out] */ DWORD __RPC_FAR * pState)
{
	PY_GATEWAY_METHOD;
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("GetState", &result);
	if (FAILED(hr)) return hr;
	// Process the Python results, and convert back to the real params
	if (!PyArg_Parse(result, "i" , pState)) return PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGRemoteDebugApplicationThread::Suspend(
		/* [out] */ DWORD __RPC_FAR * pdwCount)
{
	PY_GATEWAY_METHOD;
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("Suspend", &result);
	if (FAILED(hr)) return hr;
	// Process the Python results, and convert back to the real params
	if (!PyArg_Parse(result, "i" , pdwCount)) return PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGRemoteDebugApplicationThread::Resume(
		/* [out] */ DWORD __RPC_FAR * pdwCount)
{
	PY_GATEWAY_METHOD;
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("Resume", &result);
	if (FAILED(hr)) return hr;
	// Process the Python results, and convert back to the real params
	if (!PyArg_Parse(result, "i" , pdwCount)) return PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGRemoteDebugApplicationThread::GetSuspendCount(
		/* [out] */ DWORD __RPC_FAR * pdwCount)
{
	PY_GATEWAY_METHOD;
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("GetSuspendCount", &result);
	if (FAILED(hr)) return hr;
	// Process the Python results, and convert back to the real params
	if (!PyArg_Parse(result, "i" , pdwCount)) return PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	Py_DECREF(result);
	return hr;
}
