// This file implements the IDebugDocumentHelper Interface and Gateway for Python.
// Generated by makegw.py

#include "stdafx.h"
#include "PythonCOM.h"
#include "PythonCOMServer.h"
#include "PyIDebugDocumentHelper.h"

// @doc - This file contains autoduck documentation
// ---------------------------------------------------
//
// Interface Implementation

PyIDebugDocumentHelper::PyIDebugDocumentHelper(IUnknown *pdisp):
	PyIUnknown(pdisp)
{
	ob_type = &type;
}

PyIDebugDocumentHelper::~PyIDebugDocumentHelper()
{
}

/* static */ IDebugDocumentHelper *PyIDebugDocumentHelper::GetI(PyObject *self)
{
	return (IDebugDocumentHelper *)PyIUnknown::GetI(self);
}

// @pymethod |PyIDebugDocumentHelper|Init|Description of Init.
PyObject *PyIDebugDocumentHelper::Init(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	// @pyparm <o PyIDebugApplication>|pda||Description for pda
	// @pyparm <o unicode>|pszShortName||Description for pszShortName
	// @pyparm <o unicode>|pszLongName||Description for pszLongName
	// @pyparm int|docAttr||Description for docAttr
	PyObject *obpda;
	PyObject *obpszShortName;
	PyObject *obpszLongName;
	IDebugApplication *pda;
	BSTR pszShortName;
	BSTR pszLongName;
	TEXT_DOC_ATTR docAttr;
	if ( !PyArg_ParseTuple(args, "OOOi:Init", &obpda, &obpszShortName, &obpszLongName, &docAttr) )
		return NULL;
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_BstrFromPyObject(obpszShortName, &pszShortName)) bPythonIsHappy = FALSE;
	if (!PyCom_BstrFromPyObject(obpszLongName, &pszLongName)) bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) return NULL;
	if (!PyCom_InterfaceFromPyInstanceOrObject(obpda, IID_IDebugApplication, (void **)&pda, FALSE /* bNoneOK */))
		 bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->Init( pda, pszShortName, pszLongName, docAttr );
	pda->Release();
	if (pszShortName) SysFreeString(pszShortName);
	if (pszLongName) SysFreeString(pszLongName);
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;

}

// @pymethod |PyIDebugDocumentHelper|Attach|Add the document to the doc tree
PyObject *PyIDebugDocumentHelper::Attach(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	// @pyparm <o PyIDebugDocumentHelper>|pddhParent||Parent item.  If none, this item is top level.
	PyObject *obpddhParent;
	IDebugDocumentHelper *pddhParent;
	if ( !PyArg_ParseTuple(args, "O:Attach", &obpddhParent) )
		return NULL;
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_InterfaceFromPyInstanceOrObject(obpddhParent, IID_IDebugDocumentHelper, (void **)&pddhParent, TRUE /* bNoneOK */))
		 bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->Attach( pddhParent );
	if (pddhParent) pddhParent->Release();
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;

}

// @pymethod |PyIDebugDocumentHelper|Detach|Description of Detach.
PyObject *PyIDebugDocumentHelper::Detach(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	if ( !PyArg_ParseTuple(args, ":Detach") )
		return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->Detach( );
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;

}

// @pymethod |PyIDebugDocumentHelper|AddUnicodeText|Description of AddUnicodeText.
PyObject *PyIDebugDocumentHelper::AddUnicodeText(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	// @pyparm <o unicode>|pszText||Description for pszText
	PyObject *obpszText;
	BSTR pszText;
	if ( !PyArg_ParseTuple(args, "O:AddUnicodeText", &obpszText) )
		return NULL;
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_BstrFromPyObject(obpszText, &pszText)) bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->AddUnicodeText( pszText );
	if (pszText) SysFreeString(pszText);
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;

}

// @pymethod |PyIDebugDocumentHelper|AddDBCSText|Description of AddDBCSText.
PyObject *PyIDebugDocumentHelper::AddDBCSText(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	char *szText;
	if ( !PyArg_ParseTuple(args, "z:AddDBCSText", &szText) )
		return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->AddDBCSText( szText );
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;

}

// @pymethod |PyIDebugDocumentHelper|SetDebugDocumentHost|Description of SetDebugDocumentHost.
PyObject *PyIDebugDocumentHelper::SetDebugDocumentHost(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	// @pyparm <o PyIDebugDocumentHost>|pddh||Description for pddh
	PyObject *obpddh;
	IDebugDocumentHost *pddh;
	if ( !PyArg_ParseTuple(args, "O:SetDebugDocumentHost", &obpddh) )
		return NULL;
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_InterfaceFromPyInstanceOrObject(obpddh, IID_IDebugDocumentHost, (void **)&pddh, FALSE /* bNoneOK */))
		 bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->SetDebugDocumentHost( pddh );
	pddh->Release();
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;

}

// @pymethod |PyIDebugDocumentHelper|AddDeferredText|Description of AddDeferredText.
PyObject *PyIDebugDocumentHelper::AddDeferredText(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	// @pyparm int|cChars||Description for cChars
	// @pyparm int|dwTextStartCookie||Description for dwTextStartCookie
	ULONG cChars;
	DWORD dwTextStartCookie;
	if ( !PyArg_ParseTuple(args, "ii:AddDeferredText", &cChars, &dwTextStartCookie) )
		return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->AddDeferredText( cChars, dwTextStartCookie );
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;

}

// @pymethod |PyIDebugDocumentHelper|DefineScriptBlock|Description of DefineScriptBlock.
PyObject *PyIDebugDocumentHelper::DefineScriptBlock(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	// @pyparm int|ulCharOffset||Description for ulCharOffset
	// @pyparm int|cChars||Description for cChars
	// @pyparm <o PyIActiveScript>|pas||Description for pas
	// @pyparm int|fScriptlet||Description for fScriptlet
	PyObject *obpas;
	ULONG ulCharOffset;
	ULONG cChars;
	IActiveScript *pas;
	BOOL fScriptlet;
#ifdef _WIN64
	DWORDLONG pdwSourceContext;
#else
	DWORD pdwSourceContext;
#endif
	if ( !PyArg_ParseTuple(args, "iiOi:DefineScriptBlock", &ulCharOffset, &cChars, &obpas, &fScriptlet) )
		return NULL;
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_InterfaceFromPyInstanceOrObject(obpas, IID_IActiveScript, (void **)&pas, FALSE /* bNoneOK */))
		 bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->DefineScriptBlock( ulCharOffset, cChars, pas, fScriptlet, &pdwSourceContext );
	pas->Release();
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);

	PyObject *pyretval = Py_BuildValue("i", pdwSourceContext);
	return pyretval;
}

// @pymethod |PyIDebugDocumentHelper|SetDefaultTextAttr|Description of SetDefaultTextAttr.
PyObject *PyIDebugDocumentHelper::SetDefaultTextAttr(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	// @pyparm int|staTextAttr||Description for staTextAttr
	SOURCE_TEXT_ATTR staTextAttr;
	if ( !PyArg_ParseTuple(args, "i:SetDefaultTextAttr", &staTextAttr) )
		return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->SetDefaultTextAttr( staTextAttr );
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;
}

// @pymethod |PyIDebugDocumentHelper|SetTextAttributes|Description of SetTextAttributes.
PyObject *PyIDebugDocumentHelper::SetTextAttributes(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	// @pyparm int|ulCharOffset||Description for ulCharOffset
	// @pyparm object|obAttr||A sequence of attributes.
	ULONG ulCharOffset;
	PyObject *obAttr;
	if ( !PyArg_ParseTuple(args, "iO:SetTextAttributes", &ulCharOffset, &obAttr) )
		return NULL;
	ULONG attrlen;
	if (!PyAXDebug_PySOURCE_TEXT_ATTR_Length( obAttr, &attrlen ))
		return NULL;
	SOURCE_TEXT_ATTR *pstaTextAttr = new SOURCE_TEXT_ATTR[attrlen];
	if (pstaTextAttr==NULL) {
		PyErr_SetString(PyExc_MemoryError, "Allocating SOURCE_TEXT_ATTR array");
		return NULL;
	}
	if (!PyAXDebug_PyObject_AsSOURCE_TEXT_ATTR(obAttr, pstaTextAttr, attrlen)) {
		delete [] pstaTextAttr;
		return NULL;
	}
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->SetTextAttributes( ulCharOffset, attrlen, pstaTextAttr );
	delete [] pstaTextAttr;
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;
}

// @pymethod |PyIDebugDocumentHelper|SetLongName|Description of SetLongName.
PyObject *PyIDebugDocumentHelper::SetLongName(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	// @pyparm <o unicode>|pszLongName||Description for pszLongName
	PyObject *obpszLongName;
	BSTR pszLongName;
	if ( !PyArg_ParseTuple(args, "O:SetLongName", &obpszLongName) )
		return NULL;
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_BstrFromPyObject(obpszLongName, &pszLongName)) bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->SetLongName( pszLongName );
	if (pszLongName) SysFreeString(pszLongName);
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;

}

// @pymethod |PyIDebugDocumentHelper|SetShortName|Description of SetShortName.
PyObject *PyIDebugDocumentHelper::SetShortName(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	// @pyparm <o unicode>|pszShortName||Description for pszShortName
	PyObject *obpszShortName;
	BSTR pszShortName;
	if ( !PyArg_ParseTuple(args, "O:SetShortName", &obpszShortName) )
		return NULL;
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_BstrFromPyObject(obpszShortName, &pszShortName)) bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->SetShortName( pszShortName );
	if (pszShortName) SysFreeString(pszShortName);
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;

}

// @pymethod |PyIDebugDocumentHelper|SetDocumentAttr|Description of SetDocumentAttr.
PyObject *PyIDebugDocumentHelper::SetDocumentAttr(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	// @pyparm int|pszAttributes||Description for pszAttributes
	TEXT_DOC_ATTR pszAttributes;
	if ( !PyArg_ParseTuple(args, "i:SetDocumentAttr", &pszAttributes) )
		return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->SetDocumentAttr( pszAttributes );
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;

}

// @pymethod |PyIDebugDocumentHelper|GetDebugApplicationNode|Description of GetDebugApplicationNode.
PyObject *PyIDebugDocumentHelper::GetDebugApplicationNode(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	IDebugApplicationNode *ppdan;
	if ( !PyArg_ParseTuple(args, ":GetDebugApplicationNode") )
		return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->GetDebugApplicationNode( &ppdan );
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	return PyCom_PyObjectFromIUnknown(ppdan, IID_IDebugApplicationNode, FALSE);
}

// @pymethod |PyIDebugDocumentHelper|GetScriptBlockInfo|Description of GetScriptBlockInfo.
PyObject *PyIDebugDocumentHelper::GetScriptBlockInfo(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	// @pyparm int|dwSourceContext||Description for dwSourceContext
	DWORD dwSourceContext;
	IActiveScript *ppasd;
	ULONG piCharPos;
	ULONG pcChars;
	if ( !PyArg_ParseTuple(args, "i:GetScriptBlockInfo", &dwSourceContext) )
		return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->GetScriptBlockInfo( dwSourceContext, &ppasd, &piCharPos, &pcChars );
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	PyObject *obppasd = PyCom_PyObjectFromIUnknown(ppasd, IID_IActiveScript, FALSE);
	return Py_BuildValue("Nii", obppasd, piCharPos, pcChars);
}

// @pymethod |PyIDebugDocumentHelper|CreateDebugDocumentContext|Description of CreateDebugDocumentContext.
PyObject *PyIDebugDocumentHelper::CreateDebugDocumentContext(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	// @pyparm int|iCharPos||Description for iCharPos
	// @pyparm int|cChars||Description for cChars
	ULONG iCharPos;
	ULONG cChars;
	IDebugDocumentContext *ppddc;
	if ( !PyArg_ParseTuple(args, "ii:CreateDebugDocumentContext", &iCharPos, &cChars) )
		return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->CreateDebugDocumentContext( iCharPos, cChars, &ppddc );
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	return PyCom_PyObjectFromIUnknown(ppddc, IID_IDebugDocumentContext, FALSE);
}

// @pymethod |PyIDebugDocumentHelper|BringDocumentToTop|Description of BringDocumentToTop.
PyObject *PyIDebugDocumentHelper::BringDocumentToTop(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	if ( !PyArg_ParseTuple(args, ":BringDocumentToTop") )
		return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->BringDocumentToTop( );
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;

}

// @pymethod |PyIDebugDocumentHelper|BringDocumentContextToTop|Description of BringDocumentContextToTop.
PyObject *PyIDebugDocumentHelper::BringDocumentContextToTop(PyObject *self, PyObject *args)
{
	PY_INTERFACE_METHOD;
	IDebugDocumentHelper *pIDDH = GetI(self);
	if ( pIDDH == NULL )
		return NULL;
	// @pyparm <o PyIDebugDocumentContext>|pddc||Description for pddc
	PyObject *obpddc;
	IDebugDocumentContext *pddc;
	if ( !PyArg_ParseTuple(args, "O:BringDocumentContextToTop", &obpddc) )
		return NULL;
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_InterfaceFromPyInstanceOrObject(obpddc, IID_IDebugDocumentContext, (void **)&pddc, FALSE /* bNoneOK */))
		 bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIDDH->BringDocumentContextToTop( pddc );
	pddc->Release();
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return OleSetOleError(hr);
	Py_INCREF(Py_None);
	return Py_None;

}

// @object PyIDebugDocumentHelper|Description of the interface
static struct PyMethodDef PyIDebugDocumentHelper_methods[] =
{
	{ "Init", PyIDebugDocumentHelper::Init, 1 }, // @pymeth Init|Description of Init
	{ "Attach", PyIDebugDocumentHelper::Attach, 1 }, // @pymeth Attach|Add the document to the doc tree
	{ "Detach", PyIDebugDocumentHelper::Detach, 1 }, // @pymeth Detach|Description of Detach
	{ "AddUnicodeText", PyIDebugDocumentHelper::AddUnicodeText, 1 }, // @pymeth AddUnicodeText|Description of AddUnicodeText
	{ "AddDBCSText", PyIDebugDocumentHelper::AddDBCSText, 1 }, // @pymeth AddDBCSText|Description of AddDBCSText
	{ "SetDebugDocumentHost", PyIDebugDocumentHelper::SetDebugDocumentHost, 1 }, // @pymeth SetDebugDocumentHost|Description of SetDebugDocumentHost
	{ "AddDeferredText", PyIDebugDocumentHelper::AddDeferredText, 1 }, // @pymeth AddDeferredText|Description of AddDeferredText
	{ "DefineScriptBlock", PyIDebugDocumentHelper::DefineScriptBlock, 1 }, // @pymeth DefineScriptBlock|Description of DefineScriptBlock
	{ "SetDefaultTextAttr", PyIDebugDocumentHelper::SetDefaultTextAttr, 1 }, // @pymeth SetDefaultTextAttr|Description of SetDefaultTextAttr
	{ "SetTextAttributes", PyIDebugDocumentHelper::SetTextAttributes, 1 }, // @pymeth SetTextAttributes|Description of SetTextAttributes
	{ "SetLongName", PyIDebugDocumentHelper::SetLongName, 1 }, // @pymeth SetLongName|Description of SetLongName
	{ "SetShortName", PyIDebugDocumentHelper::SetShortName, 1 }, // @pymeth SetShortName|Description of SetShortName
	{ "SetDocumentAttr", PyIDebugDocumentHelper::SetDocumentAttr, 1 }, // @pymeth SetDocumentAttr|Description of SetDocumentAttr
	{ "GetDebugApplicationNode", PyIDebugDocumentHelper::GetDebugApplicationNode, 1 }, // @pymeth GetDebugApplicationNode|Description of GetDebugApplicationNode
	{ "GetScriptBlockInfo", PyIDebugDocumentHelper::GetScriptBlockInfo, 1 }, // @pymeth GetScriptBlockInfo|Description of GetScriptBlockInfo
	{ "CreateDebugDocumentContext", PyIDebugDocumentHelper::CreateDebugDocumentContext, 1 }, // @pymeth CreateDebugDocumentContext|Description of CreateDebugDocumentContext
	{ "BringDocumentToTop", PyIDebugDocumentHelper::BringDocumentToTop, 1 }, // @pymeth BringDocumentToTop|Description of BringDocumentToTop
	{ "BringDocumentContextToTop", PyIDebugDocumentHelper::BringDocumentContextToTop, 1 }, // @pymeth BringDocumentContextToTop|Description of BringDocumentContextToTop
	{ NULL }
};

PyComTypeObject PyIDebugDocumentHelper::type("PyIDebugDocumentHelper",
		&PyIUnknown::type,
		sizeof(PyIDebugDocumentHelper),
		PyIDebugDocumentHelper_methods,
		GET_PYCOM_CTOR(PyIDebugDocumentHelper));
// ---------------------------------------------------
//
// Gateway Implementation

STDMETHODIMP PyGDebugDocumentHelper::Init(
		/* [in] */ IDebugApplication __RPC_FAR * pda,
		/* [string][in] */ LPCOLESTR pszShortName,
		/* [string][in] */ LPCOLESTR pszLongName,
		/* [in] */ TEXT_DOC_ATTR docAttr)
{
	PY_GATEWAY_METHOD;
	PyObject *obpda;
	PyObject *obpszShortName;
	PyObject *obpszLongName;
	obpda = PyCom_PyObjectFromIUnknown(pda, IID_IDebugApplication, TRUE);
	obpszShortName = PyWinObject_FromOLECHAR(pszShortName);
	obpszLongName = PyWinObject_FromOLECHAR(pszLongName);
	HRESULT hr=InvokeViaPolicy("Init", NULL, "OOOi", obpda, obpszShortName, obpszLongName, docAttr);
	Py_XDECREF(obpda);
	Py_XDECREF(obpszShortName);
	Py_XDECREF(obpszLongName);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::Attach(
		/* [in] */ IDebugDocumentHelper __RPC_FAR * pddhParent)
{
	PY_GATEWAY_METHOD;
	PyObject *obpddhParent;
	obpddhParent = PyCom_PyObjectFromIUnknown(pddhParent, IID_IDebugDocumentHelper, TRUE);
	HRESULT hr=InvokeViaPolicy("Attach", NULL, "O", obpddhParent);
	Py_XDECREF(obpddhParent);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::Detach(
		void)
{
	PY_GATEWAY_METHOD;
	HRESULT hr=InvokeViaPolicy("Detach", NULL);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::AddUnicodeText(
		/* [string][in] */ LPCOLESTR pszText)
{
	PY_GATEWAY_METHOD;
	PyObject *obpszText;
	obpszText = PyWinObject_FromOLECHAR(pszText);
	HRESULT hr=InvokeViaPolicy("AddUnicodeText", NULL, "O", obpszText);
	Py_XDECREF(obpszText);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::AddDBCSText(
		/* [string][in] */ LPCSTR pszText)
{
	PY_GATEWAY_METHOD;
	HRESULT hr=InvokeViaPolicy("AddDBCSText", NULL, "z", pszText);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::SetDebugDocumentHost(
		/* [in] */ IDebugDocumentHost __RPC_FAR * pddh)
{
	PY_GATEWAY_METHOD;
	PyObject *obpddh;
	obpddh = PyCom_PyObjectFromIUnknown(pddh, IID_IDebugDocumentHost, TRUE);
	HRESULT hr=InvokeViaPolicy("SetDebugDocumentHost", NULL, "O", obpddh);
	Py_XDECREF(obpddh);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::AddDeferredText(
		/* [in] */ ULONG cChars,
		/* [in] */ DWORD dwTextStartCookie)
{
	PY_GATEWAY_METHOD;
	HRESULT hr=InvokeViaPolicy("AddDeferredText", NULL, "ii", cChars, dwTextStartCookie);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::DefineScriptBlock(
		/* [in] */ ULONG ulCharOffset,
		/* [in] */ ULONG cChars,
		/* [in] */ IActiveScript __RPC_FAR * pas,
		/* [in] */ BOOL fScriptlet,
#ifdef _WIN64
		/* [out] */ DWORDLONG __RPC_FAR * pdwSourceContext)
#else
		/* [out] */ DWORD __RPC_FAR * pdwSourceContext)
#endif
{
	PY_GATEWAY_METHOD;
	PyObject *obpas;
	obpas = PyCom_PyObjectFromIUnknown(pas, IID_IActiveScript, TRUE);
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("DefineScriptBlock", &result, "iiOi", ulCharOffset, cChars, obpas, fScriptlet);
	Py_XDECREF(obpas);
	if (FAILED(hr)) return hr;
	// Process the Python results, and convert back to the real params
	if (!PyArg_Parse(result, "i" , pdwSourceContext)) return PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::SetDefaultTextAttr(
		/* [in] */ SOURCE_TEXT_ATTR staTextAttr)
{
	PY_GATEWAY_METHOD;
	HRESULT hr=InvokeViaPolicy("SetDefaultTextAttr", NULL, "i", staTextAttr);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::SetTextAttributes(
		/* [in] */ ULONG ulCharOffset,
		/* [in] */ ULONG cChars,
		/* [size_is][length_is][in] */ SOURCE_TEXT_ATTR __RPC_FAR * pstaTextAttr)
{
	PY_GATEWAY_METHOD;
	PyObject *obAttr = PyAXDebug_PyObject_FromSOURCE_TEXT_ATTR(pstaTextAttr, cChars);
	HRESULT hr=InvokeViaPolicy("SetTextAttributes", NULL, "iO", ulCharOffset, obAttr);
	Py_XDECREF(obAttr);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::SetLongName(
		/* [string][in] */ LPCOLESTR pszLongName)
{
	PY_GATEWAY_METHOD;
	PyObject *obpszLongName;
	obpszLongName = PyWinObject_FromOLECHAR(pszLongName);
	HRESULT hr=InvokeViaPolicy("SetLongName", NULL, "O", obpszLongName);
	Py_XDECREF(obpszLongName);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::SetShortName(
		/* [string][in] */ LPCOLESTR pszShortName)
{
	PY_GATEWAY_METHOD;
	PyObject *obpszShortName;
	obpszShortName = PyWinObject_FromOLECHAR(pszShortName);
	HRESULT hr=InvokeViaPolicy("SetShortName", NULL, "O", obpszShortName);
	Py_XDECREF(obpszShortName);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::SetDocumentAttr(
		/* [in] */ TEXT_DOC_ATTR pszAttributes)
{
	PY_GATEWAY_METHOD;
	HRESULT hr=InvokeViaPolicy("SetDocumentAttr", NULL, "i", pszAttributes);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::GetDebugApplicationNode(
		/* [out] */ IDebugApplicationNode __RPC_FAR *__RPC_FAR * ppdan)
{
	PY_GATEWAY_METHOD;
	if (ppdan==NULL) return E_POINTER;
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("GetDebugApplicationNode", &result);
	if (FAILED(hr)) return hr;
	// Process the Python results, and convert back to the real params
	PyObject *obppdan;
	if (!PyArg_Parse(result, "O" , &obppdan)) return PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_InterfaceFromPyInstanceOrObject(obppdan, IID_IDebugApplicationNode, (void **)ppdan, FALSE /* bNoneOK */))
		 bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) hr = PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::GetScriptBlockInfo(
#ifdef _WIN64
		/* [in] */ DWORDLONG dwSourceContext,
#else
		/* [in] */ DWORD dwSourceContext,
#endif
		/* [out] */ IActiveScript __RPC_FAR *__RPC_FAR * ppasd,
		/* [out] */ ULONG __RPC_FAR * piCharPos,
		/* [out] */ ULONG __RPC_FAR * pcChars)
{
	PY_GATEWAY_METHOD;
	if (ppasd==NULL) return E_POINTER;
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("GetScriptBlockInfo", &result, "i", dwSourceContext);
	if (FAILED(hr)) return hr;
	// Process the Python results, and convert back to the real params
	PyObject *obppasd;
	if (!PyArg_ParseTuple(result, "Oii" , &obppasd, piCharPos, pcChars)) return PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_InterfaceFromPyInstanceOrObject(obppasd, IID_IActiveScript, (void **)ppasd, FALSE /* bNoneOK */))
		 bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) hr = PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::CreateDebugDocumentContext(
		/* [in] */ ULONG iCharPos,
		/* [in] */ ULONG cChars,
		/* [out] */ IDebugDocumentContext __RPC_FAR *__RPC_FAR * ppddc)
{
	PY_GATEWAY_METHOD;
	if (ppddc==NULL) return E_POINTER;
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("CreateDebugDocumentContext", &result, "ii", iCharPos, cChars);
	if (FAILED(hr)) return hr;
	// Process the Python results, and convert back to the real params
	PyObject *obppddc;
	if (!PyArg_Parse(result, "O" , &obppddc)) return PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_InterfaceFromPyInstanceOrObject(obppddc, IID_IDebugDocumentContext, (void **)ppddc, FALSE /* bNoneOK */))
		 bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) hr = PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::BringDocumentToTop(
		void)
{
	PY_GATEWAY_METHOD;
	HRESULT hr=InvokeViaPolicy("BringDocumentToTop", NULL);
	return hr;
}

STDMETHODIMP PyGDebugDocumentHelper::BringDocumentContextToTop(
		/* [in] */ IDebugDocumentContext __RPC_FAR * pddc)
{
	PY_GATEWAY_METHOD;
	PyObject *obpddc;
	obpddc = PyCom_PyObjectFromIUnknown(pddc, IID_IDebugDocumentContext, TRUE);
	HRESULT hr=InvokeViaPolicy("BringDocumentContextToTop", NULL, "O", obpddc);
	Py_XDECREF(obpddc);
	return hr;
}

