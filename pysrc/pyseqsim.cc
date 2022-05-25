//
//  seqsim module
//

#include <Python.h>
#include <structmember.h>
//#include "p3compat.h"

#include "pyseqsim.hh"

#define MyArg_ParseTupleAndKeywords(args,kwds,fmt,kwlist,...) PyArg_ParseTupleAndKeywords(args,kwds,fmt,const_cast<char**>(kwlist),__VA_ARGS__)

#include "beamseq.icc"
#include "controlseq.icc"

#define IS_PY3K

//
//  Module methods
//
//

static PyObject* pyseqsim_help(PyObject* self_o, PyObject* args)
{
  printf("Help!\n");
  return Py_None;
}

static PyMethodDef PyseqsimMethods[] = {
    {"help"  , (PyCFunction)pyseqsim_help  , METH_VARARGS, "Help Function"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

#ifdef IS_PY3K
static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "pyseqsim",
        NULL,
        -1,
        PyseqsimMethods,
        NULL,
        NULL,
        NULL,
        NULL
};
#endif

//
//  Module initialization
//

#define INITERROR return NULL

//DECLARE_INIT(pyseqsim)
PyMODINIT_FUNC
PyInit_pyseqsim(void)
{
  if (PyType_Ready(&beamseq_type) < 0)
    INITERROR; 

  if (PyType_Ready(&controlseq_type) < 0)
    INITERROR; 

#ifdef IS_PY3K
  PyObject *m = PyModule_Create(&moduledef);
#else
  PyObject *m = Py_InitModule("pyseqsim", PyseqsimMethods);
#endif
  if (m == NULL)
    INITERROR;

  Py_INCREF(&beamseq_type);
  PyModule_AddObject(m, "beamseq" , (PyObject*)&beamseq_type);

  Py_INCREF(&controlseq_type);
  PyModule_AddObject(m, "controlseq" , (PyObject*)&controlseq_type);

#ifdef IS_PY3K
  return m;
#endif
}
