// This file implements the IHTMLOMWindowServices Interface and Gateway for Python.
// Generated by makegw.py

#include "internet_pch.h"
#include "MsHtmHst.h"
#include "PyIHTMLOMWindowServices.h"

// @doc - This file contains autoduck documentation
// Gateway Implementation
STDMETHODIMP PyGHTMLOMWindowServices::moveTo(
		/* [in] */ LONG x,
		/* [in] */ LONG y)
{
	PY_GATEWAY_METHOD;
	return InvokeViaPolicy("moveTo", NULL, "ll", x, y);
}

STDMETHODIMP PyGHTMLOMWindowServices::moveBy(
		/* [in] */ LONG x,
		/* [in] */ LONG y)
{
	PY_GATEWAY_METHOD;
	return InvokeViaPolicy("moveBy", NULL, "ll", x, y);
}

STDMETHODIMP PyGHTMLOMWindowServices::resizeTo(
		/* [in] */ LONG x,
		/* [in] */ LONG y)
{
	PY_GATEWAY_METHOD;
	return InvokeViaPolicy("resizeTo", NULL, "ll", x, y);
}

STDMETHODIMP PyGHTMLOMWindowServices::resizeBy(
		/* [in] */ LONG x,
		/* [in] */ LONG y)
{
	PY_GATEWAY_METHOD;
	return InvokeViaPolicy("resizeBy", NULL, "ll", x, y);
}
