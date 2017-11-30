#include "Python.h"

#ifdef STACKLESS
#include "core/stackless_impl.h"

#ifdef WITH_THREAD
#include "pythread.h"
#endif

/******************************************************

  The Bomb object -- making exceptions convenient

 ******************************************************/

static PyBombObject *free_list = NULL;
static int numfree = 0;         /* number of bombs currently in free_list */
#define MAXFREELIST 20          /* max value for numfree */
static PyBombObject *mem_bomb = NULL; /* a permanent bomb to use for memory errors */

static void
bomb_dealloc(PyBombObject *bomb)
{
    _PyObject_GC_UNTRACK(bomb);
    Py_XDECREF(bomb->curexc_type);
    Py_XDECREF(bomb->curexc_value);
    Py_XDECREF(bomb->curexc_traceback);
    if (numfree < MAXFREELIST) {
        ++numfree;
        bomb->curexc_type = (PyObject *) free_list;
        free_list = bomb;
    }
    else
        PyObject_GC_Del(bomb);
}

static int
bomb_traverse(PyBombObject *bomb, visitproc visit, void *arg)
{
    Py_VISIT(bomb->curexc_type);
    Py_VISIT(bomb->curexc_value);
    Py_VISIT(bomb->curexc_traceback);
    return 0;
}

static void
bomb_clear(PyBombObject *bomb)
{
    Py_CLEAR(bomb->curexc_type);
    Py_CLEAR(bomb->curexc_value);
    Py_CLEAR(bomb->curexc_traceback);
}

static PyBombObject *
new_bomb(void)
{
    PyBombObject *bomb;

    if (free_list == NULL) {
        bomb = PyObject_GC_New(PyBombObject, &PyBomb_Type);
        if (bomb == NULL)
            return NULL;
    }
    else {
        assert(numfree > 0);
        --numfree;
        bomb = free_list;
        free_list = (PyBombObject *) free_list->curexc_type;
        _Py_NewReference((PyObject *) bomb);
    }
    bomb->curexc_type = NULL;
    bomb->curexc_value = NULL;
    bomb->curexc_traceback = NULL;
    PyObject_GC_Track(bomb);
    return bomb;
}

static PyObject *
bomb_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"type", "value", "traceback", NULL};
    PyBombObject *bomb = new_bomb();

    if (bomb == NULL)
        return NULL;

    if (PyTuple_GET_SIZE(args) == 1 &&
        PyTuple_Check(PyTuple_GET_ITEM(args, 0)))
        args = PyTuple_GET_ITEM(args, 0);
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOO:bomb", kwlist,
                                     &bomb->curexc_type,
                                     &bomb->curexc_value,
                                     &bomb->curexc_traceback)) {
        Py_DECREF(bomb);
        return NULL;
    }
    Py_XINCREF(bomb->curexc_type);
    Py_XINCREF(bomb->curexc_value);
    Py_XINCREF(bomb->curexc_traceback);
    return (PyObject*) bomb;
}

PyObject *
slp_make_bomb(PyObject *klass, PyObject *args, char *msg)
{
    PyBombObject *bomb;
    PyObject *tup;

    if (! (PyObject_IsSubclass(klass, PyExc_BaseException) == 1 ||
           PyString_Check(klass) ) ) {
        char s[256];

        sprintf(s, "%.128s needs Exception or string"
                   " subclass as first parameter", msg);
        TYPE_ERROR(s, NULL);
    }
    if ( (bomb = new_bomb()) == NULL)
        return NULL;
    Py_INCREF(klass);
    bomb->curexc_type = klass;
    tup = Py_BuildValue(PyTuple_Check(args) ? "O" : "(O)", args);
    bomb->curexc_value = tup;
    if (tup == NULL) {
        Py_DECREF(bomb);
        return NULL;
    }
    return (PyObject *) bomb;
}

PyObject *
slp_exc_to_bomb(PyObject *exc, PyObject *val, PyObject *tb)
{
    PyBombObject *bomb;

    /* normalize the exceptions according to "raise" semantics */
    if (tb && tb != Py_None && !PyTraceBack_Check(tb)) {
        PyErr_SetString(PyExc_TypeError,
            "third argument must be a traceback object");
        return NULL;
    }
    if (PyExceptionClass_Check(exc)) {
        ; /* it will be normalized on other side */
        /*PyErr_NormalizeException(&typ, &val, &tb);*/
    } else if (PyExceptionInstance_Check(exc)) {
        /* Raising an instance.  The value should be a dummy. */
        if (val && val != Py_None) {
            PyErr_SetString(PyExc_TypeError,
                "instance exception may not have a separate value");
            return NULL;
        }
        /* Normalize to raise <class>, <instance> */
        val = exc;
        exc = PyExceptionInstance_Class(exc);
    } else {
        /* Not something you can raise.  throw() fails. */
        PyErr_Format(PyExc_TypeError,
            "exceptions must be classes, or instances, not %s",
            Py_TYPE(exc)->tp_name);
        return NULL;
    }

    bomb = new_bomb();
    if (bomb == NULL)
        return NULL;

    Py_XINCREF(exc);
    Py_XINCREF(val);
    Py_XINCREF(tb);
    bomb->curexc_type = exc;
    bomb->curexc_value = val;
    bomb->curexc_traceback = tb;
    return (PyObject *) bomb;
}

PyObject *
slp_curexc_to_bomb(void)
{
    PyBombObject *bomb;
    if (PyErr_ExceptionMatches(PyExc_MemoryError)) {
        bomb = mem_bomb;
        Py_INCREF(bomb);
    } else
        bomb = new_bomb();
    if (bomb != NULL)
        PyErr_Fetch(&bomb->curexc_type, &bomb->curexc_value,
                    &bomb->curexc_traceback);
    return (PyObject *) bomb;
}

/* create a memory error bomb and clear the exception state */
PyObject *
slp_nomemory_bomb(void)
{
    PyErr_NoMemory();
    return slp_curexc_to_bomb();
}

/* set exception, consume bomb reference and return NULL */

PyObject *
slp_bomb_explode(PyObject *_bomb)
{
    PyBombObject* bomb = (PyBombObject*)_bomb;

    assert(PyBomb_Check(bomb));
    Py_XINCREF(bomb->curexc_type);
    Py_XINCREF(bomb->curexc_value);
    Py_XINCREF(bomb->curexc_traceback);
    PyErr_Restore(bomb->curexc_type, bomb->curexc_value,
                  bomb->curexc_traceback);
    Py_DECREF(bomb);
    return NULL;
}

static PyObject *
bomb_reduce(PyBombObject *bomb)
{
    PyObject *tup;

    tup = slp_into_tuple_with_nulls(&bomb->curexc_type, 3);
    if (tup != NULL)
        tup = Py_BuildValue("(O()O)", &PyBomb_Type, tup);
    return tup;
}

static PyObject *
bomb_setstate(PyBombObject *bomb, PyObject *args)
{
    if (PyTuple_GET_SIZE(args) != 4)
        VALUE_ERROR("bad exception tuple for bomb", NULL);
    bomb_clear(bomb);
    slp_from_tuple_with_nulls(&bomb->curexc_type, args);
    Py_INCREF(bomb);
    return (PyObject *) bomb;
}

static PyMemberDef bomb_members[] = {
    {"type",            T_OBJECT, offsetof(PyBombObject, curexc_type), READONLY},
    {"value",           T_OBJECT, offsetof(PyBombObject, curexc_value), READONLY},
    {"traceback",       T_OBJECT, offsetof(PyBombObject, curexc_traceback), READONLY},
    {0}
};

static PyMethodDef bomb_methods[] = {
    {"__reduce__",              (PyCFunction)bomb_reduce,       METH_NOARGS},
    {"__reduce_ex__",           (PyCFunction)bomb_reduce,       METH_VARARGS},
    {"__setstate__",            (PyCFunction)bomb_setstate,     METH_O},
    {NULL,     NULL}             /* sentinel */
};

PyDoc_STRVAR(bomb__doc__,
"A bomb object is used to hold exceptions in tasklets.\n\
Whenever a tasklet is activated and its tempval is a bomb,\n\
it will explode as an exception.\n\
\n\
You can create a bomb by hand and attach it to a tasklet if you like.\n\
Note that bombs are 'sloppy' about the argument list, which means that\n\
the following works, although you should use '*sys.exc_info()'.\n\
\n\
from stackless import *; import sys\n\
t = tasklet(lambda:42)()\n\
try: 1/0\n\
except: b = bomb(sys.exc_info())\n\
\n\
t.tempval = b\n\
t.run()  # let the bomb explode");

PyTypeObject PyBomb_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "_stackless.bomb",
    sizeof(PyBombObject),
    0,
    (destructor)bomb_dealloc,                   /* tp_dealloc */
    0,                                          /* tp_print */
    0,                                          /* tp_getattr */
    0,                                          /* tp_setattr */
    0,                                          /* tp_compare */
    0,                                          /* tp_repr */
    0,                                          /* tp_as_number */
    0,                                          /* tp_as_sequence */
    0,                                          /* tp_as_mapping */
    0,                                          /* tp_hash */
    0,                                          /* tp_call */
    0,                                          /* tp_str */
    PyObject_GenericGetAttr,                    /* tp_getattro */
    PyObject_GenericSetAttr,                    /* tp_setattro */
    0,                                          /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC, /* tp_flags */
    bomb__doc__,                                /* tp_doc */
    (traverseproc)bomb_traverse,                /* tp_traverse */
    (inquiry) bomb_clear,                       /* tp_clear */
    0,                                          /* tp_richcompare */
    0,                                          /* tp_weaklistoffset */
    0,                                          /* tp_iter */
    0,                                          /* tp_iternext */
    bomb_methods,                               /* tp_methods */
    bomb_members,                               /* tp_members */
    0,                                          /* tp_getset */
    0,                                          /* tp_base */
    0,                                          /* tp_dict */
    0,                                          /* tp_descr_get */
    0,                                          /* tp_descr_set */
    0,                                          /* tp_dictoffset */
    0,                                          /* tp_init */
    0,                                          /* tp_alloc */
    bomb_new,                                   /* tp_new */
    _PyObject_GC_Del,                           /* tp_free */
};

int
slp_init_bombtype(void)
{
    if (PyType_Ready(&PyBomb_Type))
        return -1;
    /* allocate the permanent bomb to use for mem errors */
    mem_bomb = new_bomb();
    return mem_bomb ? 0 : -1;
}

/*******************************************************************

  Exception handling revised.

  Every tasklet has its own exception state. The thread state
  exists only once for the current thread, so we need to simulate
  ownership.

  Whenever a tasklet is run for the first time, it should clear
  the exception variables and start with a clean state.

  When it dies normally, it should clean up these.

  When a transfer occours from one tasklet to another,
  the first tasklet should save its exception in local variables,
  and the other one should restore its own.

  When a tasklet dies with an uncaught exception, this will
  be passed on to the main tasklet. The main tasklet must
  clear its exception state, if any, and take over those of
  the tasklet resting in peace.

  2002-08-08 This was a misconception. This is not the current
  exception, but the one which ceval provides for exception
  handlers. That means, sharing of this variable is totally
  unrelated to the current error, and we always swap the data.

  Added support for trace/profile as well.

 ********************************************************************/

slp_schedule_hook_func *_slp_schedule_fasthook;
PyObject *_slp_schedule_hook;

typedef struct {
    intptr_t magic1;
    PyTaskletTStateStruc s;
    intptr_t magic2;
} saved_tstat_with_magic_t;

/* not a valid ptr and not a common integer */
#define SAVED_TSTATE_MAGIC1 (((intptr_t)transfer_with_exc)+1)
#define SAVED_TSTATE_MAGIC2 (-1*((intptr_t)transfer_with_exc))
saved_tstat_with_magic_t * _dont_optimise_away_saved_tstat_with_magic;

static int
transfer_with_exc(PyCStackObject **cstprev, PyCStackObject *cst, PyTaskletObject *prev)
{
    PyThreadState *ts = PyThreadState_GET();
    int ret;

    saved_tstat_with_magic_t sm;
    sm.magic1 = SAVED_TSTATE_MAGIC1;
    sm.magic2 = SAVED_TSTATE_MAGIC2;

    /* prevent overly compiler optimisation.
    We store the address of sm into a global variable.
    This way the optimizer can't change the layout of the structure. */
    _dont_optimise_away_saved_tstat_with_magic = &sm;

    sm.s.tracing = ts->tracing;
    sm.s.c_profilefunc = ts->c_profilefunc;
    sm.s.c_tracefunc = ts->c_tracefunc;
    sm.s.c_profileobj = ts->c_profileobj;
    sm.s.c_traceobj = ts->c_traceobj;
    Py_XINCREF(sm.s.c_profileobj);
    Py_XINCREF(sm.s.c_traceobj);

    sm.s.exc_type = ts->exc_type;
    sm.s.exc_value = ts->exc_value;
    sm.s.exc_traceback = ts->exc_traceback;

    PyEval_SetTrace(NULL, NULL);
    PyEval_SetProfile(NULL, NULL);
    ts->tracing = 0;
    ts->exc_type = ts->exc_value = ts->exc_traceback = NULL;

    ret = slp_transfer(cstprev, cst, prev);

    ts->tracing = sm.s.tracing;
    PyEval_SetTrace(sm.s.c_tracefunc, sm.s.c_traceobj);
    PyEval_SetProfile(sm.s.c_profilefunc, sm.s.c_profileobj);

    ts->exc_type = sm.s.exc_type;
    ts->exc_value = sm.s.exc_value;
    ts->exc_traceback = sm.s.exc_traceback;

    sm.magic1 = 0;
    sm.magic2 = 0;
    Py_XDECREF(sm.s.c_profileobj);
    Py_XDECREF(sm.s.c_traceobj);

    return ret;
}

PyTaskletTStateStruc *
slp_get_saved_tstate(PyTaskletObject *task) {
    /* typical offset of the structure from cstate->stack
     * is about 20. Therefore 100 should be enough */
    static const Py_ssize_t max_search_size = 100;
    PyCStackObject *cst = task->cstate;
    Py_ssize_t *p, *p_max;

    if (cst->tstate && cst->tstate->st.current == task)
        /* task is current */
        return NULL;
    if (cst->task != task)
        return NULL;
    assert(cst->ob_size >= 0);
    if (cst->ob_size > max_search_size)
        p_max = &(cst->stack[max_search_size]);
    else
        p_max = &(cst->stack[cst->ob_size]);
    for (p=cst->stack; p!=p_max; p++) {
        if (SAVED_TSTATE_MAGIC1 == *p) {
            saved_tstat_with_magic_t *sm = (saved_tstat_with_magic_t *)p;
            assert(sm->magic1 == SAVED_TSTATE_MAGIC1);
            if (sm->magic2 == SAVED_TSTATE_MAGIC2)
                /* got it */
                return &(sm->s);
        }
    }
    return NULL;
}

/* scheduler monitoring */

int
slp_schedule_callback(PyTaskletObject *prev, PyTaskletObject *next)
{
    PyObject *args;

    if (prev == NULL) prev = (PyTaskletObject *)Py_None;
    if (next == NULL) next = (PyTaskletObject *)Py_None;
    args = Py_BuildValue("(OO)", prev, next);
    if (args != NULL) {
        PyObject *type, *value, *traceback, *ret;

        PyErr_Fetch(&type, &value, &traceback);
        ret = PyObject_Call(_slp_schedule_hook, args, NULL);
        if (ret != NULL)
            PyErr_Restore(type, value, traceback);
        else {
            Py_XDECREF(type);
            Py_XDECREF(value);
            Py_XDECREF(traceback);
        }
        Py_XDECREF(ret);
        Py_DECREF(args);
        return ret ? 0 : -1;
    }
    else
        return -1;
}

static void
slp_call_schedule_fasthook(PyThreadState *ts, PyTaskletObject *prev, PyTaskletObject *next)
{
    int ret;
    PyObject *tmp;
    PyTaskletObject * old_current;
    if (ts->st.schedlock) {
        Py_FatalError("Recursive scheduler call due to callbacks!");
        return;
    }
    /* store the del post-switch for the duration.  We don't want code
     * to cause the "prev" tasklet to disappear
     */
    tmp = ts->st.del_post_switch;
    ts->st.del_post_switch = NULL;

    ts->st.schedlock = 1;
    old_current = ts->st.current;
    if (prev)
        ts->st.current = prev;
    ret = _slp_schedule_fasthook(prev, next);
    ts->st.current = old_current;
    ts->st.schedlock = 0;
    if (ret) {
        PyObject *msg = PyString_FromString("Error in scheduling callback");
        if (msg == NULL)
            msg = Py_None;
        /* the following can have side effects, hence it is good to have
         * del_post_switch tucked away
         */
        PyErr_WriteUnraisable(msg);
        if (msg != Py_None)
            Py_DECREF(msg);
        PyErr_Clear();
    }
    assert(ts->st.del_post_switch == 0);
    ts->st.del_post_switch = tmp;
}

#define NOTIFY_SCHEDULE(prev, next, errflag) \
    if (_slp_schedule_fasthook != NULL) { \
        slp_call_schedule_fasthook(ts, prev, next); \
    }

static void
kill_wrap_bad_guy(PyTaskletObject *prev, PyTaskletObject *bad_guy)
{
    /*
     * just in case a transfer didn't work, we pack the bad
     * tasklet into the exception and remove it from the runnables.
     *
     */
    PyThreadState *ts = PyThreadState_GET();
    PyObject *newval = PyTuple_New(2);
    if (bad_guy->next != NULL) {
        ts->st.current = bad_guy;
        slp_current_remove();
    }
    /* restore last tasklet */
    if (prev->next == NULL)
        slp_current_insert(prev);
    ts->frame = prev->f.frame;
    ts->st.current = prev;
    if (newval != NULL) {
        /* merge bad guy into exception */
        PyObject *exc, *val, *tb;
        PyErr_Fetch(&exc, &val, &tb);
        PyTuple_SET_ITEM(newval, 0, val);
        PyTuple_SET_ITEM(newval, 1, (PyObject*)bad_guy);
        Py_INCREF(bad_guy);
        PyErr_Restore(exc, newval, tb);
    }
}

/* slp_schedule_task is moved down and merged with soft switching */

/* non-recursive scheduling */

PyObject *
slp_restore_exception(PyFrameObject *f, int exc, PyObject *retval)
{
    PyThreadState *ts = PyThreadState_GET();
    PyCFrameObject *cf = (PyCFrameObject *) f;

    f = cf->f_back;
    ts->exc_type = cf->ob1;
    ts->exc_value = cf->ob2;
    ts->exc_traceback = cf->ob3;
    cf->ob1 = cf->ob2 = cf->ob3 = NULL;
    Py_DECREF(cf);
    ts->frame = f;
    return STACKLESS_PACK(ts, retval);
}

PyObject *
slp_restore_tracing(PyFrameObject *f, int exc, PyObject *retval)
{
    PyThreadState *ts = PyThreadState_GET();
    PyCFrameObject *cf = (PyCFrameObject *) f;

    f = cf->f_back;
    if (NULL == cf->any1 && NULL == cf->any2) {
        /* frame was created by unpickling */
        if (cf->n & 1) {
            Py_tracefunc func = slp_get_sys_trace_func();
            if (NULL == func)
                return NULL;
            cf->any1 = func;
        }
        if (cf->n & 2) {
            Py_tracefunc func = slp_get_sys_profile_func();
            if (NULL == func)
                return NULL;
            cf->any2 = func;
        }
    }
    ts->tracing = cf->i;
    PyEval_SetTrace((Py_tracefunc)cf->any1, cf->ob1);
    PyEval_SetProfile((Py_tracefunc)cf->any2, cf->ob2);
    Py_DECREF(cf);
    ts->frame = f;
    return STACKLESS_PACK(ts, retval);
}

int
slp_encode_ctrace_functions(Py_tracefunc c_tracefunc, Py_tracefunc c_profilefunc)
{
    int encoded = 0;
    if (c_tracefunc) {
        Py_tracefunc func = slp_get_sys_trace_func();
        if (NULL == func)
            return -1;
        encoded |= (c_tracefunc == func)<<0;
    }
    if (c_profilefunc) {
        Py_tracefunc func = slp_get_sys_profile_func();
        if (NULL == func)
            return -1;
        encoded |= (c_profilefunc == func)<<1;
    }
    return encoded;
}

/* jumping from a soft tasklet to a hard switched */

static PyObject *
jump_soft_to_hard(PyFrameObject *f, int exc, PyObject *retval)
{
    PyThreadState *ts = PyThreadState_GET();

    ts->frame = f->f_back;

    /* reinstate the del_post_switch */
    assert(ts->st.del_post_switch == NULL);
    ts->st.del_post_switch = ((PyCFrameObject*)f)->ob1;
    ((PyCFrameObject*)f)->ob1 = NULL;

    Py_DECREF(f);
    /* ignore retval. everything is in the tasklet. */
    Py_DECREF(retval); /* consume ref according to protocol */
    slp_transfer_return(ts->st.current->cstate);
    /* we either have an error or don't come back, so: */
    return NULL;
}


/* combined soft/hard switching */

int
slp_ensure_linkage(PyTaskletObject *t)
{
    if (t->cstate->task == t)
        return 0;
    assert(t->cstate->tstate != NULL);
    if (!slp_cstack_new(&t->cstate, t->cstate->tstate->st.cstack_base, t))
        return -1;
    t->cstate->nesting_level = 0;
    return 0;
}


/* check whether a different thread can be run */

static int
is_thread_runnable(PyThreadState *ts)
{
#ifdef WITH_THREAD
    if (ts == PyThreadState_GET())
        return 0;
    return !ts->st.thread.is_blocked;
#endif
    return 0;
}

static int
check_for_deadlock(void)
{
    PyThreadState *ts = PyThreadState_GET();
    PyInterpreterState *interp = ts->interp;

    /* see if anybody else will be able to run */

    for (ts = interp->tstate_head; ts != NULL; ts = ts->next)
        if (is_thread_runnable(ts))
            return 0;
    return 1;
}

static PyObject *
make_deadlock_bomb(void)
{
    PyErr_SetString(PyExc_RuntimeError,
        "Deadlock: the last runnable tasklet cannot be blocked.");
    return slp_curexc_to_bomb();
}

#ifdef WITH_THREAD

/* make sure that locks live longer than their threads */

static void
destruct_lock(PyObject *capsule)
{
    PyThread_type_lock lock = PyCapsule_GetPointer(capsule, 0);
    if (lock) {
        PyThread_acquire_lock(lock, 0);
        PyThread_release_lock(lock);
        PyThread_free_lock(lock);
    }
}

static PyObject *
new_lock(void)
{
    PyThread_type_lock lock;

    lock = PyThread_allocate_lock();
    if (lock == NULL) return NULL;

    return PyCapsule_New(lock, 0, destruct_lock);
}

#define get_lock(obj) PyCapsule_GetPointer(obj, 0)

#define acquire_lock(lock, flag) PyThread_acquire_lock(get_lock(lock), flag)
#define release_lock(lock) PyThread_release_lock(get_lock(lock))

static int schedule_thread_block(PyThreadState *ts)
{
    assert(!ts->st.thread.is_blocked);
    assert(ts->st.runcount == 0);
    /* create on demand the lock we use to block */
    if (ts->st.thread.block_lock == NULL) {
        if (!(ts->st.thread.block_lock = new_lock()))
            return -1;
        acquire_lock(ts->st.thread.block_lock, 1);
    }

    /* block */
    ts->st.thread.is_blocked = 1;
    ts->st.thread.is_idle = 1;
    Py_BEGIN_ALLOW_THREADS
    acquire_lock(ts->st.thread.block_lock, 1);
    Py_END_ALLOW_THREADS
    ts->st.thread.is_idle = 0;


    return 0;
}

static void schedule_thread_unblock(PyThreadState *nts)
{
    if (nts->st.thread.is_blocked) {
        nts->st.thread.is_blocked = 0;
        release_lock(nts->st.thread.block_lock);
    }
}

void slp_thread_unblock(PyThreadState *nts)
{
    schedule_thread_unblock(nts);
}

#else

void slp_thread_unblock(PyThreadState *nts)
{}

#endif

static int
schedule_task_block(PyObject **result, PyTaskletObject *prev, int stackless, int *did_switch)
{
    PyThreadState *ts = PyThreadState_GET();
    PyObject *retval, *tmpval=NULL;
    PyTaskletObject *next = NULL;
    int fail, revive_main = 0;
    PyTaskletObject *wakeup;

    /* which "main" do we awaken if we are blocking? */
    wakeup = slp_get_watchdog(ts, 0);

#ifdef WITH_THREAD
    if ( !(ts->st.runflags & Py_WATCHDOG_THREADBLOCK) && wakeup->next == NULL)
        /* we also must never block if watchdog is running not in threadblocking mode */
        revive_main = 1;

    if (revive_main)
        assert(wakeup->next == NULL); /* target must be floating */
#endif

    if (revive_main || check_for_deadlock()) {
        goto cantblock;
    }
#ifdef WITH_THREAD
    for(;;) {
        /* store the frame back in the tasklet while we thread block, so that
         * e.g. insert doesn't think that it is dead
         */
        if (prev->f.frame == 0) {
            prev->f.frame = ts->frame;
            fail = schedule_thread_block(ts);
            prev->f.frame = 0;
        } else
            fail = schedule_thread_block(ts);
        if (fail)
            return fail;

        /* We should have a "current" tasklet, but it could have been removed
         * by the other thread in the time this thread reacquired the gil.
         */
        next = ts->st.current;
        if (next) {
            /* don't "remove" it because that will make another tasklet "current" */
            Py_INCREF(next);
            break;
        }
        if (check_for_deadlock())
            goto cantblock;
    }
#else
    next = prev;
    Py_INCREF(next);
#endif
    /* this must be after releasing the locks because of hard switching */
    fail = slp_schedule_task(result, prev, next, stackless, did_switch);
    Py_DECREF(next);

    /* Now we may have switched (on this thread), clear any post-switch stuff.
     * We may have a valuable "tmpval" here
     * because of channel switching, so be careful to maintain that.
     */
    if (! fail && ts->st.del_post_switch) {
        PyObject *tmp;
        TASKLET_CLAIMVAL(ts->st.current, &tmp);
        Py_CLEAR(ts->st.del_post_switch);
        TASKLET_SETVAL_OWN(ts->st.current, tmp);
    }
    return fail;

cantblock:
    /* cannot block */
    if (revive_main || (ts == slp_initial_tstate && wakeup->next == NULL)) {
        /* emulate old revive_main behavior:
         * passing a value only if it is an exception
         */
        if (PyBomb_Check(prev->tempval)) {
            TASKLET_CLAIMVAL(wakeup, &tmpval);
            TASKLET_SETVAL(wakeup, prev->tempval);
        }
        fail = slp_schedule_task(result, prev, wakeup, stackless, did_switch);
        if (fail && tmpval != NULL)
            TASKLET_SETVAL_OWN(wakeup, tmpval);
        else
            Py_XDECREF(tmpval);
        return fail;
    }
    if (!(retval = make_deadlock_bomb()))
        return -1;
    TASKLET_CLAIMVAL(wakeup, &tmpval);
    TASKLET_SETVAL_OWN(prev, retval);
    fail = slp_schedule_task(result, prev, prev, stackless, did_switch);
    if (fail && tmpval != NULL)
        TASKLET_SETVAL_OWN(wakeup, tmpval);
    else
        Py_XDECREF(tmpval);
    return fail;
}

#ifdef WITH_THREAD
static int
schedule_task_interthread(PyObject **result,
                            PyTaskletObject *prev,
                            PyTaskletObject *next,
                            int stackless,
                            int *did_switch)
{
    PyThreadState *nts = next->cstate->tstate;
    int fail;

    /* get myself ready, since the previous task is going to continue on the
     * current thread
     */
    if (nts == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "tasklet has no thread");
        return -1;
    }
    fail = slp_schedule_task(result, prev, prev, stackless, did_switch);
    if (fail)
        return fail;

    /* put the next tasklet in the target thread's queue */
   if (next->flags.blocked) {
        /* unblock from channel */
        slp_channel_remove_slow(next, NULL, NULL, NULL);
        slp_current_insert(next);
    }
    else if (next->next == NULL) {
        /* reactivate floating task */
        Py_INCREF(next);
        slp_current_insert(next);
    }

    /* unblock the thread if required */
    schedule_thread_unblock(nts);

    return 0;
}

#endif

/* deal with soft interrupts by modifying next to specify the main tasklet */
static void slp_schedule_soft_irq(PyThreadState *ts, PyTaskletObject *prev,
                                                   PyTaskletObject **next, int not_now)
{
    PyTaskletObject *tmp;
    PyTaskletObject *watchdog;
    assert(*next);
    if(!prev->flags.pending_irq || !(ts->st.runflags & PY_WATCHDOG_SOFT) )
        return; /* no soft interrupt pending */

    watchdog = slp_get_watchdog(ts, 1);

    prev->flags.pending_irq = 0;

    if (watchdog->next != NULL)
        return; /* target isn't floating, we are probably raising an exception */

    /* if were were switching to or from our target, we don't do anything */
    if (prev == watchdog || *next == watchdog)
        return;

    if (not_now || !TASKLET_NESTING_OK(prev)) {
        /* pass the irq flag to the next tasklet */
        (*next)->flags.pending_irq = 1;
        return;
    }

    /* Soft interrupt.  Signal that an interrupt took place by placing
     * the "next" tasklet into interrupted (it would have been run) */
    assert(ts->st.interrupted == NULL);
    ts->st.interrupted = (PyObject*)*next;
    Py_INCREF(ts->st.interrupted);

    /* restore main.  insert it before the old next, so that the old next get
     * run after it
     */
    tmp = ts->st.current;
    ts->st.current = *next;
    slp_current_insert(watchdog);
    Py_INCREF(watchdog);
    ts->st.current = tmp;

    *next = watchdog;
}


static int
slp_schedule_task_prepared(PyThreadState *ts, PyObject **result, PyTaskletObject *prev,
                        PyTaskletObject *next, int stackless,
                        int *did_switch);


int
slp_schedule_task(PyObject **result, PyTaskletObject *prev, PyTaskletObject *next, int stackless,
                  int *did_switch)
{
    PyThreadState *ts = PyThreadState_GET();
    PyChannelObject *u_chan = NULL;
    PyTaskletObject *u_next;
    int u_dir;
    int inserted = 0;
    int fail;

    *result = NULL;
    if (did_switch)
        *did_switch = 0; /* only set this if an actual switch occurs */

    if (next == NULL)
        return schedule_task_block(result, prev, stackless, did_switch);

#ifdef WITH_THREAD
    /* note that next->cstate is undefined if it is ourself.
       Also note, that prev->cstate->tstate == NULL during Py_Finalize() */
    assert(prev->cstate == NULL || prev->cstate->tstate == NULL || prev->cstate->tstate == ts);
    /* The last condition is required during shutdown when next->cstate->tstate == NULL */
    if (next->cstate != NULL && next->cstate->tstate != ts && next != prev) {
        return schedule_task_interthread(result, prev, next, stackless, did_switch);
    }
#endif

    /* switch trap. We don't trap on interthread switches because they
     * don't cause a switch on the local thread.
     */
    if (ts->st.switch_trap) {
        if (prev != next) {
            PyErr_SetString(PyExc_RuntimeError, "switch_trap");
            return -1;
        }
    }

    /* prepare the new tasklet */
    if (next->flags.blocked) {
        /* unblock from channel */
        slp_channel_remove_slow(next, &u_chan, &u_dir, &u_next);
        slp_current_insert(next);
        inserted = 1;
    }
    else if (next->next == NULL) {
        /* reactivate floating task */
        Py_INCREF(next);
        slp_current_insert(next);
        inserted = 1;
    }

    fail = slp_schedule_task_prepared(ts, result, prev, next, stackless, did_switch);
    if (fail && inserted) {
        slp_current_uninsert(next);
        if (u_chan)
            slp_channel_insert(u_chan, next, u_dir, u_next);
        else
            Py_DECREF(next);
    }
    return fail;
}

static int
slp_schedule_task_prepared(PyThreadState *ts, PyObject **result, PyTaskletObject *prev, PyTaskletObject *next, int stackless,
                  int *did_switch)
{
    PyCStackObject **cstprev;

    PyObject *retval;
    int (*transfer)(PyCStackObject **, PyCStackObject *, PyTaskletObject *);

    /* remove the no-soft-irq flag from the runflags */
    int no_soft_irq = ts->st.runflags & PY_WATCHDOG_NO_SOFT_IRQ;
    ts->st.runflags &= ~PY_WATCHDOG_NO_SOFT_IRQ;

    slp_schedule_soft_irq(ts, prev, &next, no_soft_irq);

    if (prev == next) {
        TASKLET_CLAIMVAL(prev, &retval);
        if (PyBomb_Check(retval))
            retval = slp_bomb_explode(retval);
        *result = retval;
        return 0;
    }

    NOTIFY_SCHEDULE(prev, next, -1);

    if (!(ts->st.runflags & PY_WATCHDOG_TOTALTIMEOUT))
        ts->st.ticker = ts->st.interval; /* reset timeslice */
    prev->recursion_depth = ts->recursion_depth;
    prev->f.frame = ts->frame;

    if (!stackless || ts->st.nesting_level != 0)
        goto hard_switching;

    /* start of soft switching code */

    if (prev->cstate != ts->st.initial_stub) {
        Py_DECREF(prev->cstate);
        prev->cstate = ts->st.initial_stub;
        Py_INCREF(prev->cstate);
    }
    if (ts != slp_initial_tstate) {
        /* ensure to get all tasklets into the other thread's chain */
        if (slp_ensure_linkage(prev) || slp_ensure_linkage(next))
            return -1;
    }

    /* handle exception */
    if (ts->exc_type == Py_None) {
        Py_XDECREF(ts->exc_type);
        ts->exc_type = NULL;
    }
    if (ts->exc_type != NULL) {
        /* build a shadow frame if we are returning here*/
        if (ts->frame != NULL) {
            PyCFrameObject *f = slp_cframe_new(slp_restore_exception, 1);
            if (f == NULL)
                return -1;
            f->ob1 = ts->exc_type;
            f->ob2 = ts->exc_value;
            f->ob3 = ts->exc_traceback;
            prev->f.frame = (PyFrameObject *) f;
        }
        ts->exc_type = ts->exc_value =
                           ts->exc_traceback = NULL;
    }
    if (ts->use_tracing || ts->tracing) {
        /* build a shadow frame if we are returning here */
        if (prev->f.frame != NULL) {
            PyCFrameObject *f = slp_cframe_new(slp_restore_tracing, 0);
            int c_functions = slp_encode_ctrace_functions(ts->c_tracefunc, ts->c_profilefunc);
            if (f == NULL || c_functions == -1)
                return -1;
            f->f_back = prev->f.frame;
            Py_XINCREF(f->f_back);
            f->any1 = ts->c_tracefunc;
            f->any2 = ts->c_profilefunc;
            f->i = ts->tracing;
            f->n = c_functions;
            assert(NULL == f->ob1);
            assert(NULL == f->ob2);
            f->ob1 = ts->c_traceobj;
            f->ob2 = ts->c_profileobj;
            Py_XINCREF(f->ob1);
            Py_XINCREF(f->ob2);
            prev->f.frame = (PyFrameObject *) f;
        }
        PyEval_SetTrace(NULL, NULL);
        PyEval_SetProfile(NULL, NULL);
        ts->tracing = 0;
    }
    assert(next->cstate != NULL);

    if (next->cstate->nesting_level != 0) {
        /* can soft switch out of this tasklet, but the target tasklet
         * was in a hard switched state, so we need a helper frame to
         * jump to the destination stack
         */
        PyFrameObject *tmp1 = ts->frame, *tmp2 = next->f.frame;
        ts->frame = next->f.frame;
        next->f.frame = NULL;
        ts->frame = (PyFrameObject *)
                    slp_cframe_new(jump_soft_to_hard, 1);
        if (ts->frame == NULL) {
            ts->frame = tmp1;
            next->f.frame = tmp2;
            return -1;
        }
         /* Move the del_post_switch into the cframe for it to resurrect it.
         * switching isn't complete until after it has run
         */
        ((PyCFrameObject*)ts->frame)->ob1 = ts->st.del_post_switch;
        ts->st.del_post_switch = NULL;

        /* note that we don't explode any bomb now and leave it in next->tempval */
        /* retval will be ignored eventually */
        retval = next->tempval;
        Py_INCREF(retval);
    } else {
        /* regular soft switching */
        assert(next->f.frame);
        ts->frame = next->f.frame;
        next->f.frame = NULL;
        TASKLET_CLAIMVAL(next, &retval);
        if (PyBomb_Check(retval))
            retval = slp_bomb_explode(retval);
    }
    /* no failure possible from here on */
    ts->recursion_depth = next->recursion_depth;
    ts->st.current = next;
    if (did_switch)
        *did_switch = 1;
    *result = STACKLESS_PACK(ts, retval);
    return 0;

hard_switching:
    /* since we change the stack we must assure that the protocol was met */
    STACKLESS_ASSERT();

    /* note: nesting_level is handled in cstack_new */
    cstprev = &prev->cstate;

    ts->st.current = next;

    if (ts->exc_type == Py_None) {
        Py_XDECREF(ts->exc_type);
        ts->exc_type = NULL;
    }
    ts->recursion_depth = next->recursion_depth;
    ts->frame = next->f.frame;
    next->f.frame = NULL;

    ++ts->st.nesting_level;
    if (ts->exc_type != NULL || ts->use_tracing || ts->tracing)
        transfer = transfer_with_exc;
    else
        transfer = slp_transfer;

    if (transfer(cstprev, next->cstate, prev) >= 0) {
        --ts->st.nesting_level;
        TASKLET_CLAIMVAL(prev, &retval);
        if (PyBomb_Check(retval))
            retval = slp_bomb_explode(retval);
        if (did_switch)
            *did_switch = 1;
        *result = retval;

        /* Now evaluate any pending pending slp_restore_tracing cframes.
           They were inserted by tasklet_set_trace_function or
           tasklet_set_profile_function */
        if (prev->cstate->nesting_level > 0) {
            PyCFrameObject *f = (PyCFrameObject *)(ts->frame);
            if (f && PyCFrame_Check(f) && f->f_execute == slp_restore_tracing) {
                PyObject *retval;

                /* the next frame must be a real frame */
                assert(f->f_back && PyFrame_Check(f->f_back));

                /* Hack: call the eval frame function directly */
                retval = slp_restore_tracing((PyFrameObject *)f, 0, Py_None);
                STACKLESS_UNPACK(ts, retval);
                if (NULL == retval)
                    return -1;
                assert(PyFrame_Check(ts->frame));
            }
        }

        return 0;
    }
    else {
        --ts->st.nesting_level;
        kill_wrap_bad_guy(prev, next);
        return -1;
    }
}

int
slp_initialize_main_and_current(void)
{
    PyThreadState *ts = PyThreadState_GET();
    PyTaskletObject *task;

    /* refuse executing main in an unhandled error context */
    if (! (PyErr_Occurred() == NULL || PyErr_Occurred() == Py_None) ) {
#ifdef _DEBUG
        PyObject *type, *value, *traceback;
        PyErr_Fetch(&type, &value, &traceback);
        Py_XINCREF(type);
        Py_XINCREF(value);
        Py_XINCREF(traceback);
        PyErr_Restore(type, value, traceback);
        printf("Pending error while entering Stackless subsystem:\n");
        PyErr_Print();
        printf("Above exception is re-raised to the caller.\n");
        PyErr_Restore(type, value, traceback);
#endif
    return 1;
    }

    task = (PyTaskletObject *) PyTasklet_Type.tp_new(
                &PyTasklet_Type, NULL, NULL);
    if (task == NULL) return -1;
    assert(task->cstate != NULL);
    ts->st.main = task;
    Py_INCREF(task);
    slp_current_insert(task);
    ts->st.current = task;

    NOTIFY_SCHEDULE(NULL, task, -1);

    return 0;
}


/* scheduling and destructing the previous one.  This function
 * "steals" the reference to "prev" (the current) because we may never
 * return to the caller.  _unless_ there is an error. In case of error
 * the caller still owns the reference.  This is not normal python behaviour
 * (ref semantics should be error-invariant) but necessary in the
 * never-return reality of stackless.
 */

static int
schedule_task_destruct(PyObject **retval, PyTaskletObject *prev, PyTaskletObject *next)
{
    /*
     * The problem is to leave the dying tasklet alive
     * until we have done the switch.  We use the st->ts.del_post_switch
     * field to help us with that, someone else with decref it.
     */
    PyThreadState *ts = PyThreadState_GET();
    int fail = 0;

    /* we should have no nesting level */
    assert(ts->st.nesting_level == 0);
    /* even there is a (buggy) nesting, ensure soft switch */
    if (ts->st.nesting_level != 0) {
        /* TODO: Old message with no context for what to do.  Revisit?
        printf("XXX error, nesting_level = %d\n", ts->st.nesting_level); */
        ts->st.nesting_level = 0;
    }

    /* update what's not yet updated

    Normal tasklets when created have no recursion depth yet, but the main
    tasklet is initialized in the middle of an existing indeterminate call
    stack.  Therefore it is not guaranteed that there is not a pre-existing
    recursion depth from before its initialization. So, assert that this
    is zero, or that we are the main tasklet being destroyed (see tasklet_end).
    */
    assert(ts->recursion_depth == 0 || (ts->st.main == NULL && prev == next));
    prev->recursion_depth = 0;
    assert(ts->frame == NULL);
    prev->f.frame = NULL;

    /* We are passed the last reference to "prev".
     * The tasklet can only be cleanly decrefed after we have completely
     * switched to another one, because the decref can trigger tasklet
     * swithes. this would otherwise mess up our soft switching.  Generally
     * nothing significant must happen once we are unwinding the stack.
     */
    assert(ts->st.del_post_switch == NULL);
    ts->st.del_post_switch = (PyObject*)prev;
    /* do a soft switch */
    if (prev != next) {
        int switched;
        PyObject *tuple, *tempval=NULL;
        /* A non-trivial tempval should be cleared at the earliest opportunity
         * later, to avoid reference cycles.  We can't decref it here because
         * that could cause destructors to run, violating the stackless protocol
         * So, we pack it up with the tasklet in a tuple
         */
        if (prev->tempval != Py_None) {
            TASKLET_CLAIMVAL(prev, &tempval);
            tuple = Py_BuildValue("NN", prev, tempval);
            if (tuple == NULL) {
                TASKLET_SETVAL_OWN(prev, tempval);
                return -1;
            }
            ts->st.del_post_switch = tuple;
        }
        fail = slp_schedule_task(retval, prev, next, 1, &switched);
        /* it should either fail or switch */
        if (!fail)
            assert(switched);
        if (fail) {
            /* something happened, cancel our decref manipulations. */
            if (tempval != NULL) {
                TASKLET_SETVAL(prev, tempval);
                Py_INCREF(prev);
                Py_CLEAR(ts->st.del_post_switch);
            } else
                ts->st.del_post_switch  = 0;
            return fail;
        }
    } else {
        /* main is exiting */
        TASKLET_CLAIMVAL(prev, retval);
        if (PyBomb_Check(*retval))
            *retval = slp_bomb_explode(*retval);
    }
    return fail;
}

/* defined in pythonrun.c */
extern void PyStackless_HandleSystemExit(void);
/* defined in stacklessmodule.c */
extern int PyStackless_CallErrorHandler(void);

/* ending of the tasklet.  Note that this function
 * cannot fail, the retval, in case of NULL, is just
 * the exception to be continued in the new
 * context.
 */
static PyObject *
tasklet_end(PyObject *retval)
{
    PyThreadState *ts = PyThreadState_GET();
    PyTaskletObject *task = ts->st.current;
    PyTaskletObject *next;

    int ismain = task == ts->st.main;
    int schedule_fail;

    /*
     * see whether we have a SystemExit, which is no error.
     * Note that TaskletExit is a subclass.
     * otherwise make the exception into a bomb.
     */
    if (retval == NULL) {
        int handled = 0;
        if (PyErr_ExceptionMatches(PyExc_SystemExit)) {
            /* but if it is truly a SystemExit on the main thread, we want the exit! */
            if (ts == slp_initial_tstate && !PyErr_ExceptionMatches(PyExc_TaskletExit)) {
                PyStackless_HandleSystemExit();
                handled = 1; /* handler returned, it wants us to silence it */
            } else if (!ismain) {
                /* deal with TaskletExit on a non-main tasklet */
                handled = 1;
            }
        }
        if (handled) {
            PyErr_Clear();
            Py_INCREF(Py_None);
            retval = Py_None;
        } else {
            if (!ismain) {
                /* non-main tasklets get the chance to handle errors.
                 * errors in the handlers (or a non-present one)
                 * result in the standard behaviour, transfering the error
                 * to the main tasklet
                 */
                if (!PyStackless_CallErrorHandler()) {
                    retval = Py_None;
                    Py_INCREF(Py_None);
                }
            }
            if (retval == NULL)
                retval = slp_curexc_to_bomb();
            if (retval == NULL)
                retval = slp_nomemory_bomb();
        }
    }

    /*
     * put the result back into the dead tasklet, to be retrieved
     * by schedule_task_destruct(), or cleared there
     */
    TASKLET_SETVAL(task, retval);

    if (ismain) {
        /*
         * Because of soft switching, we may find ourself in the top level of a stack that was created
         * using another stub (another entry point into stackless).  If so, we need a final return to
         * the original stub if necessary. (Meanwhile, task->cstate may be an old nesting state and not
         * the original stub, so we take the stub from the tstate)
         */
        if (ts->st.serial_last_jump != ts->st.initial_stub->serial)
            slp_transfer_return(ts->st.initial_stub);
    }

    /* remove current from runnables.  We now own its reference. */
    slp_current_remove();

    /*
     * clean up any current exception - this tasklet is dead.
     * This only happens if we are killing tasklets in the middle
     * of their execution.
     */
    if (ts->exc_type != NULL && ts->exc_type != Py_None) {
        Py_DECREF(ts->exc_type);
        Py_XDECREF(ts->exc_value);
        Py_XDECREF(ts->exc_traceback);
        ts->exc_type = ts->exc_value = ts->exc_traceback = NULL;
    }

    /* capture all exceptions */
    if (ismain) {
        /*
         * Main wants to exit. We clean up, but leave the
         * runnables chain intact.
         */
        ts->st.main = NULL;
        Py_DECREF(retval);
        schedule_fail = schedule_task_destruct(&retval, task, task);
        if (!schedule_fail)
            Py_DECREF(task); /* the reference for ts->st.main */
        else
            ts->st.main = task;
        goto end;
    }

    next = ts->st.current;
    if (next == NULL) {
        /* there is no current tasklet to wakeup.  Must wakeup watchdog or main */
        PyTaskletObject *wakeup = slp_get_watchdog(ts, 0);
        int blocked = wakeup->flags.blocked;

        /* If the target is blocked and there is no pending error,
         * we need to create a deadlock error to wake it up with.
         */
        if (blocked && !PyBomb_Check(retval)) {
            char *txt;
            PyObject *bomb;
            /* main was blocked and nobody can send */
            if (blocked < 0)
                txt = "the main tasklet is receiving"
                    " without a sender available.";
            else
                txt = "the main tasklet is sending"
                    " without a receiver available.";
            PyErr_SetString(PyExc_RuntimeError, txt);
            /* fall through to error handling */
            bomb = slp_curexc_to_bomb();
            if (bomb == NULL)
                bomb = slp_nomemory_bomb();
            Py_SETREF(retval, bomb);
            TASKLET_SETVAL(task, retval);
        }
        next = wakeup;
    }

    if (PyBomb_Check(retval)) {
        /* a bomb, due to deadlock or passed in, must wake up the correct
         * tasklet
         */
        next = slp_get_watchdog(ts, 0);
        /* Remove the bomb from the source since it is frequently the
         * source of a reference cycle
         */
        assert(task->tempval == retval);
        TASKLET_CLAIMVAL(task, &retval);
        TASKLET_SETVAL_OWN(next, retval);
    }
    Py_DECREF(retval);

    /* hand off our reference to "task" to the function */
    schedule_fail = schedule_task_destruct(&retval, task, next);
end:
    if (schedule_fail) {
        /* the api for this function does not allow for failure */
        Py_FatalError("Could not end tasklet");
        /* if it did, it would now perform a slp_current_uninsert(task)
         * since we would still own the reference to "task"
         */
    }
    return retval;
}

/*
  the following functions only have to handle "real"
  tasklets, those which need to switch the C stack.
  The "soft" tasklets are handled by frame pushing.
  It is not so much simpler than I thought :-(
*/

PyObject *
slp_run_tasklet(PyFrameObject *f)
{
    PyThreadState *ts = PyThreadState_GET();
    PyObject *retval;

    if ( (ts->st.main == NULL) && slp_initialize_main_and_current()) {
        ts->frame = NULL;
        return NULL;
    }
    ts->frame = f;

    TASKLET_CLAIMVAL(ts->st.current, &retval);

    if (PyBomb_Check(retval))
        retval = slp_bomb_explode(retval);
    while (ts->st.main != NULL) {
        /* XXX correct condition? or current? */
        retval = slp_frame_dispatch_top(retval);
        retval = tasklet_end(retval);
        if (STACKLESS_UNWINDING(retval))
            STACKLESS_UNPACK(ts, retval);
        /* if we softswitched out from the tasklet end */
        Py_CLEAR(ts->st.del_post_switch);
    }
    return retval;
}

/* Clear out the free list */

void
slp_scheduling_fini(void)
{
    while (free_list != NULL) {
        PyBombObject *bomb = free_list;
        free_list = (PyBombObject *) free_list->curexc_type;
        PyObject_GC_Del(bomb);
        --numfree;
    }
    assert(numfree == 0);
}

#endif
