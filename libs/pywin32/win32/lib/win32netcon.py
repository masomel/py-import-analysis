# Generated by h2py from lmaccess.h

# Included from lmcons.h
CNLEN = 15
LM20_CNLEN = 15
DNLEN = CNLEN
LM20_DNLEN = LM20_CNLEN
UNCLEN = (CNLEN+2)
LM20_UNCLEN = (LM20_CNLEN+2)
NNLEN = 80
LM20_NNLEN = 12
RMLEN = (UNCLEN+1+NNLEN)
LM20_RMLEN = (LM20_UNCLEN+1+LM20_NNLEN)
SNLEN = 80
LM20_SNLEN = 15
STXTLEN = 256
LM20_STXTLEN = 63
PATHLEN = 256
LM20_PATHLEN = 256
DEVLEN = 80
LM20_DEVLEN = 8
EVLEN = 16
UNLEN = 256
LM20_UNLEN = 20
GNLEN = UNLEN
LM20_GNLEN = LM20_UNLEN
PWLEN = 256
LM20_PWLEN = 14
SHPWLEN = 8
CLTYPE_LEN = 12
MAXCOMMENTSZ = 256
LM20_MAXCOMMENTSZ = 48
QNLEN = NNLEN
LM20_QNLEN = LM20_NNLEN
ALERTSZ = 128
NETBIOS_NAME_LEN = 16
CRYPT_KEY_LEN = 7
CRYPT_TXT_LEN = 8
ENCRYPTED_PWLEN = 16
SESSION_PWLEN = 24
SESSION_CRYPT_KLEN = 21
PARMNUM_ALL = 0
PARM_ERROR_NONE = 0
PARMNUM_BASE_INFOLEVEL = 1000
NULL = 0
PLATFORM_ID_DOS = 300
PLATFORM_ID_OS2 = 400
PLATFORM_ID_NT = 500
PLATFORM_ID_OSF = 600
PLATFORM_ID_VMS = 700
MAX_LANMAN_MESSAGE_ID = 5799
UF_SCRIPT = 1
UF_ACCOUNTDISABLE = 2
UF_HOMEDIR_REQUIRED = 8
UF_LOCKOUT = 16
UF_PASSWD_NOTREQD = 32
UF_PASSWD_CANT_CHANGE = 64
UF_TEMP_DUPLICATE_ACCOUNT = 256
UF_NORMAL_ACCOUNT = 512
UF_INTERDOMAIN_TRUST_ACCOUNT = 2048
UF_WORKSTATION_TRUST_ACCOUNT = 4096
UF_SERVER_TRUST_ACCOUNT = 8192
UF_MACHINE_ACCOUNT_MASK = ( UF_INTERDOMAIN_TRUST_ACCOUNT | \
                                  UF_WORKSTATION_TRUST_ACCOUNT | \
                                  UF_SERVER_TRUST_ACCOUNT )
UF_ACCOUNT_TYPE_MASK = ( \
                    UF_TEMP_DUPLICATE_ACCOUNT | \
                    UF_NORMAL_ACCOUNT | \
                    UF_INTERDOMAIN_TRUST_ACCOUNT | \
                    UF_WORKSTATION_TRUST_ACCOUNT | \
                    UF_SERVER_TRUST_ACCOUNT \
                )
UF_DONT_EXPIRE_PASSWD = 65536
UF_MNS_LOGON_ACCOUNT = 131072
UF_SETTABLE_BITS = ( \
                    UF_SCRIPT | \
                    UF_ACCOUNTDISABLE | \
                    UF_LOCKOUT | \
                    UF_HOMEDIR_REQUIRED  | \
                    UF_PASSWD_NOTREQD | \
                    UF_PASSWD_CANT_CHANGE | \
                    UF_ACCOUNT_TYPE_MASK | \
                    UF_DONT_EXPIRE_PASSWD | \
                    UF_MNS_LOGON_ACCOUNT \
                )
FILTER_TEMP_DUPLICATE_ACCOUNT = (1)
FILTER_NORMAL_ACCOUNT = (2)
FILTER_INTERDOMAIN_TRUST_ACCOUNT = (8)
FILTER_WORKSTATION_TRUST_ACCOUNT = (16)
FILTER_SERVER_TRUST_ACCOUNT = (32)
LG_INCLUDE_INDIRECT = (1)
AF_OP_PRINT = 1
AF_OP_COMM = 2
AF_OP_SERVER = 4
AF_OP_ACCOUNTS = 8
AF_SETTABLE_BITS = (AF_OP_PRINT | AF_OP_COMM | \
                                AF_OP_SERVER | AF_OP_ACCOUNTS)
UAS_ROLE_STANDALONE = 0
UAS_ROLE_MEMBER = 1
UAS_ROLE_BACKUP = 2
UAS_ROLE_PRIMARY = 3
USER_NAME_PARMNUM = 1
USER_PASSWORD_PARMNUM = 3
USER_PASSWORD_AGE_PARMNUM = 4
USER_PRIV_PARMNUM = 5
USER_HOME_DIR_PARMNUM = 6
USER_COMMENT_PARMNUM = 7
USER_FLAGS_PARMNUM = 8
USER_SCRIPT_PATH_PARMNUM = 9
USER_AUTH_FLAGS_PARMNUM = 10
USER_FULL_NAME_PARMNUM = 11
USER_USR_COMMENT_PARMNUM = 12
USER_PARMS_PARMNUM = 13
USER_WORKSTATIONS_PARMNUM = 14
USER_LAST_LOGON_PARMNUM = 15
USER_LAST_LOGOFF_PARMNUM = 16
USER_ACCT_EXPIRES_PARMNUM = 17
USER_MAX_STORAGE_PARMNUM = 18
USER_UNITS_PER_WEEK_PARMNUM = 19
USER_LOGON_HOURS_PARMNUM = 20
USER_PAD_PW_COUNT_PARMNUM = 21
USER_NUM_LOGONS_PARMNUM = 22
USER_LOGON_SERVER_PARMNUM = 23
USER_COUNTRY_CODE_PARMNUM = 24
USER_CODE_PAGE_PARMNUM = 25
USER_PRIMARY_GROUP_PARMNUM = 51
USER_PROFILE = 52
USER_PROFILE_PARMNUM = 52
USER_HOME_DIR_DRIVE_PARMNUM = 53
USER_NAME_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_NAME_PARMNUM)
USER_PASSWORD_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_PASSWORD_PARMNUM)
USER_PASSWORD_AGE_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_PASSWORD_AGE_PARMNUM)
USER_PRIV_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_PRIV_PARMNUM)
USER_HOME_DIR_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_HOME_DIR_PARMNUM)
USER_COMMENT_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_COMMENT_PARMNUM)
USER_FLAGS_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_FLAGS_PARMNUM)
USER_SCRIPT_PATH_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_SCRIPT_PATH_PARMNUM)
USER_AUTH_FLAGS_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_AUTH_FLAGS_PARMNUM)
USER_FULL_NAME_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_FULL_NAME_PARMNUM)
USER_USR_COMMENT_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_USR_COMMENT_PARMNUM)
USER_PARMS_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_PARMS_PARMNUM)
USER_WORKSTATIONS_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_WORKSTATIONS_PARMNUM)
USER_LAST_LOGON_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_LAST_LOGON_PARMNUM)
USER_LAST_LOGOFF_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_LAST_LOGOFF_PARMNUM)
USER_ACCT_EXPIRES_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_ACCT_EXPIRES_PARMNUM)
USER_MAX_STORAGE_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_MAX_STORAGE_PARMNUM)
USER_UNITS_PER_WEEK_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_UNITS_PER_WEEK_PARMNUM)
USER_LOGON_HOURS_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_LOGON_HOURS_PARMNUM)
USER_PAD_PW_COUNT_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_PAD_PW_COUNT_PARMNUM)
USER_NUM_LOGONS_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_NUM_LOGONS_PARMNUM)
USER_LOGON_SERVER_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_LOGON_SERVER_PARMNUM)
USER_COUNTRY_CODE_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_COUNTRY_CODE_PARMNUM)
USER_CODE_PAGE_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_CODE_PAGE_PARMNUM)
USER_PRIMARY_GROUP_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_PRIMARY_GROUP_PARMNUM)
USER_HOME_DIR_DRIVE_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + USER_HOME_DIR_DRIVE_PARMNUM)
NULL_USERSETINFO_PASSWD = "              "
UNITS_PER_DAY = 24
UNITS_PER_WEEK = UNITS_PER_DAY * 7
USER_PRIV_MASK = 3
USER_PRIV_GUEST = 0
USER_PRIV_USER = 1
USER_PRIV_ADMIN = 2
MAX_PASSWD_LEN = PWLEN
DEF_MIN_PWLEN = 6
DEF_PWUNIQUENESS = 5
DEF_MAX_PWHIST = 8
DEF_MAX_BADPW = 0
VALIDATED_LOGON = 0
PASSWORD_EXPIRED = 2
NON_VALIDATED_LOGON = 3
VALID_LOGOFF = 1
MODALS_MIN_PASSWD_LEN_PARMNUM = 1
MODALS_MAX_PASSWD_AGE_PARMNUM = 2
MODALS_MIN_PASSWD_AGE_PARMNUM = 3
MODALS_FORCE_LOGOFF_PARMNUM = 4
MODALS_PASSWD_HIST_LEN_PARMNUM = 5
MODALS_ROLE_PARMNUM = 6
MODALS_PRIMARY_PARMNUM = 7
MODALS_DOMAIN_NAME_PARMNUM = 8
MODALS_DOMAIN_ID_PARMNUM = 9
MODALS_LOCKOUT_DURATION_PARMNUM = 10
MODALS_LOCKOUT_OBSERVATION_WINDOW_PARMNUM = 11
MODALS_LOCKOUT_THRESHOLD_PARMNUM = 12
MODALS_MIN_PASSWD_LEN_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + MODALS_MIN_PASSWD_LEN_PARMNUM)
MODALS_MAX_PASSWD_AGE_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + MODALS_MAX_PASSWD_AGE_PARMNUM)
MODALS_MIN_PASSWD_AGE_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + MODALS_MIN_PASSWD_AGE_PARMNUM)
MODALS_FORCE_LOGOFF_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + MODALS_FORCE_LOGOFF_PARMNUM)
MODALS_PASSWD_HIST_LEN_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + MODALS_PASSWD_HIST_LEN_PARMNUM)
MODALS_ROLE_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + MODALS_ROLE_PARMNUM)
MODALS_PRIMARY_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + MODALS_PRIMARY_PARMNUM)
MODALS_DOMAIN_NAME_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + MODALS_DOMAIN_NAME_PARMNUM)
MODALS_DOMAIN_ID_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + MODALS_DOMAIN_ID_PARMNUM)
GROUPIDMASK = 32768
GROUP_ALL_PARMNUM = 0
GROUP_NAME_PARMNUM = 1
GROUP_COMMENT_PARMNUM = 2
GROUP_ATTRIBUTES_PARMNUM = 3
GROUP_ALL_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + GROUP_ALL_PARMNUM)
GROUP_NAME_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + GROUP_NAME_PARMNUM)
GROUP_COMMENT_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + GROUP_COMMENT_PARMNUM)
GROUP_ATTRIBUTES_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + GROUP_ATTRIBUTES_PARMNUM)
LOCALGROUP_NAME_PARMNUM = 1
LOCALGROUP_COMMENT_PARMNUM = 2
MAXPERMENTRIES = 64
ACCESS_NONE = 0
ACCESS_READ = 1
ACCESS_WRITE = 2
ACCESS_CREATE = 4
ACCESS_EXEC = 8
ACCESS_DELETE = 16
ACCESS_ATRIB = 32
ACCESS_PERM = 64
ACCESS_GROUP = 32768
ACCESS_AUDIT = 1
ACCESS_SUCCESS_OPEN = 16
ACCESS_SUCCESS_WRITE = 32
ACCESS_SUCCESS_DELETE = 64
ACCESS_SUCCESS_ACL = 128
ACCESS_SUCCESS_MASK = 240
ACCESS_FAIL_OPEN = 256
ACCESS_FAIL_WRITE = 512
ACCESS_FAIL_DELETE = 1024
ACCESS_FAIL_ACL = 2048
ACCESS_FAIL_MASK = 3840
ACCESS_FAIL_SHIFT = 4
ACCESS_RESOURCE_NAME_PARMNUM = 1
ACCESS_ATTR_PARMNUM = 2
ACCESS_COUNT_PARMNUM = 3
ACCESS_ACCESS_LIST_PARMNUM = 4
ACCESS_RESOURCE_NAME_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + ACCESS_RESOURCE_NAME_PARMNUM)
ACCESS_ATTR_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + ACCESS_ATTR_PARMNUM)
ACCESS_COUNT_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + ACCESS_COUNT_PARMNUM)
ACCESS_ACCESS_LIST_INFOLEVEL = \
            (PARMNUM_BASE_INFOLEVEL + ACCESS_ACCESS_LIST_PARMNUM)
ACCESS_LETTERS = "RWCXDAP         "
NETLOGON_CONTROL_QUERY = 1
NETLOGON_CONTROL_REPLICATE = 2
NETLOGON_CONTROL_SYNCHRONIZE = 3
NETLOGON_CONTROL_PDC_REPLICATE = 4
NETLOGON_CONTROL_REDISCOVER = 5
NETLOGON_CONTROL_TC_QUERY = 6
NETLOGON_CONTROL_TRANSPORT_NOTIFY = 7
NETLOGON_CONTROL_FIND_USER = 8
NETLOGON_CONTROL_UNLOAD_NETLOGON_DLL = 65531
NETLOGON_CONTROL_BACKUP_CHANGE_LOG = 65532
NETLOGON_CONTROL_TRUNCATE_LOG = 65533
NETLOGON_CONTROL_SET_DBFLAG = 65534
NETLOGON_CONTROL_BREAKPOINT = 65535
NETLOGON_REPLICATION_NEEDED = 1
NETLOGON_REPLICATION_IN_PROGRESS = 2
NETLOGON_FULL_SYNC_REPLICATION = 4
NETLOGON_REDO_NEEDED = 8

######################
# Manual stuff

TEXT=lambda x:x

MAX_PREFERRED_LENGTH = -1
PARM_ERROR_UNKNOWN = -1
MESSAGE_FILENAME = TEXT("NETMSG")
OS2MSG_FILENAME = TEXT("BASE")
HELP_MSG_FILENAME = TEXT("NETH")
BACKUP_MSG_FILENAME = TEXT("BAK.MSG")
TIMEQ_FOREVER = -1
USER_MAXSTORAGE_UNLIMITED = -1
USER_NO_LOGOFF = -1
DEF_MAX_PWAGE = TIMEQ_FOREVER
DEF_MIN_PWAGE = 0
DEF_FORCE_LOGOFF = -1
ONE_DAY = 1*24*3600
GROUP_SPECIALGRP_USERS = "USERS"
GROUP_SPECIALGRP_ADMINS = "ADMINS"
GROUP_SPECIALGRP_GUESTS = "GUESTS"
GROUP_SPECIALGRP_LOCAL = "LOCAL"
ACCESS_ALL = ( ACCESS_READ | ACCESS_WRITE | ACCESS_CREATE | ACCESS_EXEC | ACCESS_DELETE | ACCESS_ATRIB | ACCESS_PERM )

# From lmserver.h
SV_PLATFORM_ID_OS2 = 400
SV_PLATFORM_ID_NT = 500
MAJOR_VERSION_MASK = 15
SV_TYPE_WORKSTATION = 1
SV_TYPE_SERVER = 2
SV_TYPE_SQLSERVER = 4
SV_TYPE_DOMAIN_CTRL = 8
SV_TYPE_DOMAIN_BAKCTRL = 16
SV_TYPE_TIME_SOURCE = 32
SV_TYPE_AFP = 64
SV_TYPE_NOVELL = 128
SV_TYPE_DOMAIN_MEMBER = 256
SV_TYPE_PRINTQ_SERVER = 512
SV_TYPE_DIALIN_SERVER = 1024
SV_TYPE_XENIX_SERVER = 2048
SV_TYPE_SERVER_UNIX = SV_TYPE_XENIX_SERVER
SV_TYPE_NT = 4096
SV_TYPE_WFW = 8192
SV_TYPE_SERVER_MFPN = 16384
SV_TYPE_SERVER_NT = 32768
SV_TYPE_POTENTIAL_BROWSER = 65536
SV_TYPE_BACKUP_BROWSER = 131072
SV_TYPE_MASTER_BROWSER = 262144
SV_TYPE_DOMAIN_MASTER = 524288
SV_TYPE_SERVER_OSF = 1048576
SV_TYPE_SERVER_VMS = 2097152
SV_TYPE_WINDOWS = 4194304
SV_TYPE_DFS = 8388608
SV_TYPE_CLUSTER_NT = 16777216
SV_TYPE_DCE = 268435456
SV_TYPE_ALTERNATE_XPORT = 536870912
SV_TYPE_LOCAL_LIST_ONLY = 1073741824
SV_TYPE_DOMAIN_ENUM = -2147483648
SV_TYPE_ALL = -1
SV_NODISC = -1
SV_USERSECURITY = 1
SV_SHARESECURITY = 0
SV_HIDDEN = 1
SV_VISIBLE = 0
SV_PLATFORM_ID_PARMNUM = 101
SV_NAME_PARMNUM = 102
SV_VERSION_MAJOR_PARMNUM = 103
SV_VERSION_MINOR_PARMNUM = 104
SV_TYPE_PARMNUM = 105
SV_COMMENT_PARMNUM = 5
SV_USERS_PARMNUM = 107
SV_DISC_PARMNUM = 10
SV_HIDDEN_PARMNUM = 16
SV_ANNOUNCE_PARMNUM = 17
SV_ANNDELTA_PARMNUM = 18
SV_USERPATH_PARMNUM = 112
SV_ULIST_MTIME_PARMNUM = 401
SV_GLIST_MTIME_PARMNUM = 402
SV_ALIST_MTIME_PARMNUM = 403
SV_ALERTS_PARMNUM = 11
SV_SECURITY_PARMNUM = 405
SV_NUMADMIN_PARMNUM = 406
SV_LANMASK_PARMNUM = 407
SV_GUESTACC_PARMNUM = 408
SV_CHDEVQ_PARMNUM = 410
SV_CHDEVJOBS_PARMNUM = 411
SV_CONNECTIONS_PARMNUM = 412
SV_SHARES_PARMNUM = 413
SV_OPENFILES_PARMNUM = 414
SV_SESSREQS_PARMNUM = 417
SV_ACTIVELOCKS_PARMNUM = 419
SV_NUMREQBUF_PARMNUM = 420
SV_NUMBIGBUF_PARMNUM = 422
SV_NUMFILETASKS_PARMNUM = 423
SV_ALERTSCHED_PARMNUM = 37
SV_ERRORALERT_PARMNUM = 38
SV_LOGONALERT_PARMNUM = 39
SV_ACCESSALERT_PARMNUM = 40
SV_DISKALERT_PARMNUM = 41
SV_NETIOALERT_PARMNUM = 42
SV_MAXAUDITSZ_PARMNUM = 43
SV_SRVHEURISTICS_PARMNUM = 431
SV_SESSOPENS_PARMNUM = 501
SV_SESSVCS_PARMNUM = 502
SV_OPENSEARCH_PARMNUM = 503
SV_SIZREQBUF_PARMNUM = 504
SV_INITWORKITEMS_PARMNUM = 505
SV_MAXWORKITEMS_PARMNUM = 506
SV_RAWWORKITEMS_PARMNUM = 507
SV_IRPSTACKSIZE_PARMNUM = 508
SV_MAXRAWBUFLEN_PARMNUM = 509
SV_SESSUSERS_PARMNUM = 510
SV_SESSCONNS_PARMNUM = 511
SV_MAXNONPAGEDMEMORYUSAGE_PARMNUM = 512
SV_MAXPAGEDMEMORYUSAGE_PARMNUM = 513
SV_ENABLESOFTCOMPAT_PARMNUM = 514
SV_ENABLEFORCEDLOGOFF_PARMNUM = 515
SV_TIMESOURCE_PARMNUM = 516
SV_ACCEPTDOWNLEVELAPIS_PARMNUM = 517
SV_LMANNOUNCE_PARMNUM = 518
SV_DOMAIN_PARMNUM = 519
SV_MAXCOPYREADLEN_PARMNUM = 520
SV_MAXCOPYWRITELEN_PARMNUM = 521
SV_MINKEEPSEARCH_PARMNUM = 522
SV_MAXKEEPSEARCH_PARMNUM = 523
SV_MINKEEPCOMPLSEARCH_PARMNUM = 524
SV_MAXKEEPCOMPLSEARCH_PARMNUM = 525
SV_THREADCOUNTADD_PARMNUM = 526
SV_NUMBLOCKTHREADS_PARMNUM = 527
SV_SCAVTIMEOUT_PARMNUM = 528
SV_MINRCVQUEUE_PARMNUM = 529
SV_MINFREEWORKITEMS_PARMNUM = 530
SV_XACTMEMSIZE_PARMNUM = 531
SV_THREADPRIORITY_PARMNUM = 532
SV_MAXMPXCT_PARMNUM = 533
SV_OPLOCKBREAKWAIT_PARMNUM = 534
SV_OPLOCKBREAKRESPONSEWAIT_PARMNUM = 535
SV_ENABLEOPLOCKS_PARMNUM = 536
SV_ENABLEOPLOCKFORCECLOSE_PARMNUM = 537
SV_ENABLEFCBOPENS_PARMNUM = 538
SV_ENABLERAW_PARMNUM = 539
SV_ENABLESHAREDNETDRIVES_PARMNUM = 540
SV_MINFREECONNECTIONS_PARMNUM = 541
SV_MAXFREECONNECTIONS_PARMNUM = 542
SV_INITSESSTABLE_PARMNUM = 543
SV_INITCONNTABLE_PARMNUM = 544
SV_INITFILETABLE_PARMNUM = 545
SV_INITSEARCHTABLE_PARMNUM = 546
SV_ALERTSCHEDULE_PARMNUM = 547
SV_ERRORTHRESHOLD_PARMNUM = 548
SV_NETWORKERRORTHRESHOLD_PARMNUM = 549
SV_DISKSPACETHRESHOLD_PARMNUM = 550
SV_MAXLINKDELAY_PARMNUM = 552
SV_MINLINKTHROUGHPUT_PARMNUM = 553
SV_LINKINFOVALIDTIME_PARMNUM = 554
SV_SCAVQOSINFOUPDATETIME_PARMNUM = 555
SV_MAXWORKITEMIDLETIME_PARMNUM = 556
SV_MAXRAWWORKITEMS_PARMNUM = 557
SV_PRODUCTTYPE_PARMNUM = 560
SV_SERVERSIZE_PARMNUM = 561
SV_CONNECTIONLESSAUTODISC_PARMNUM = 562
SV_SHARINGVIOLATIONRETRIES_PARMNUM = 563
SV_SHARINGVIOLATIONDELAY_PARMNUM = 564
SV_MAXGLOBALOPENSEARCH_PARMNUM = 565
SV_REMOVEDUPLICATESEARCHES_PARMNUM = 566
SV_LOCKVIOLATIONRETRIES_PARMNUM = 567
SV_LOCKVIOLATIONOFFSET_PARMNUM = 568
SV_LOCKVIOLATIONDELAY_PARMNUM = 569
SV_MDLREADSWITCHOVER_PARMNUM = 570
SV_CACHEDOPENLIMIT_PARMNUM = 571
SV_CRITICALTHREADS_PARMNUM = 572
SV_RESTRICTNULLSESSACCESS_PARMNUM = 573
SV_ENABLEWFW311DIRECTIPX_PARMNUM = 574
SV_OTHERQUEUEAFFINITY_PARMNUM = 575
SV_QUEUESAMPLESECS_PARMNUM = 576
SV_BALANCECOUNT_PARMNUM = 577
SV_PREFERREDAFFINITY_PARMNUM = 578
SV_MAXFREERFCBS_PARMNUM = 579
SV_MAXFREEMFCBS_PARMNUM = 580
SV_MAXFREELFCBS_PARMNUM = 581
SV_MAXFREEPAGEDPOOLCHUNKS_PARMNUM = 582
SV_MINPAGEDPOOLCHUNKSIZE_PARMNUM = 583
SV_MAXPAGEDPOOLCHUNKSIZE_PARMNUM = 584
SV_SENDSFROMPREFERREDPROCESSOR_PARMNUM = 585
SV_MAXTHREADSPERQUEUE_PARMNUM = 586
SV_CACHEDDIRECTORYLIMIT_PARMNUM = 587
SV_MAXCOPYLENGTH_PARMNUM = 588
SV_ENABLEBULKTRANSFER_PARMNUM = 589
SV_ENABLECOMPRESSION_PARMNUM = 590
SV_AUTOSHAREWKS_PARMNUM = 591
SV_AUTOSHARESERVER_PARMNUM = 592
SV_ENABLESECURITYSIGNATURE_PARMNUM = 593
SV_REQUIRESECURITYSIGNATURE_PARMNUM = 594
SV_MINCLIENTBUFFERSIZE_PARMNUM = 595
SV_CONNECTIONNOSESSIONSTIMEOUT_PARMNUM = 596
SVI1_NUM_ELEMENTS = 5
SVI2_NUM_ELEMENTS = 40
SVI3_NUM_ELEMENTS = 44
SW_AUTOPROF_LOAD_MASK = 1
SW_AUTOPROF_SAVE_MASK = 2
SV_MAX_SRV_HEUR_LEN = 32
SV_USERS_PER_LICENSE = 5
SVTI2_REMAP_PIPE_NAMES = 2

# Generated by h2py from lmshare.h
SHARE_NETNAME_PARMNUM = 1
SHARE_TYPE_PARMNUM = 3
SHARE_REMARK_PARMNUM = 4
SHARE_PERMISSIONS_PARMNUM = 5
SHARE_MAX_USES_PARMNUM = 6
SHARE_CURRENT_USES_PARMNUM = 7
SHARE_PATH_PARMNUM = 8
SHARE_PASSWD_PARMNUM = 9
SHARE_FILE_SD_PARMNUM = 501
SHI1_NUM_ELEMENTS = 4
SHI2_NUM_ELEMENTS = 10
STYPE_DISKTREE = 0
STYPE_PRINTQ = 1
STYPE_DEVICE = 2
STYPE_IPC = 3
STYPE_SPECIAL = -2147483648
SHI1005_FLAGS_DFS = 1
SHI1005_FLAGS_DFS_ROOT = 2
COW_PERMACHINE = 4
COW_PERUSER = 8
CSC_CACHEABLE = 16
CSC_NOFLOWOPS = 32
CSC_AUTO_INWARD = 64
CSC_AUTO_OUTWARD = 128
SHI1005_VALID_FLAGS_SET = (   CSC_CACHEABLE   | \
                                    CSC_NOFLOWOPS   | \
                                    CSC_AUTO_INWARD | \
                                    CSC_AUTO_OUTWARD| \
                                    COW_PERMACHINE  | \
                                    COW_PERUSER    )
SHI1007_VALID_FLAGS_SET = SHI1005_VALID_FLAGS_SET
SESS_GUEST = 1
SESS_NOENCRYPTION = 2
SESI1_NUM_ELEMENTS = 8
SESI2_NUM_ELEMENTS = 9
PERM_FILE_READ = 1
PERM_FILE_WRITE = 2
PERM_FILE_CREATE = 4

# Generated by h2py from d:\mssdk\include\winnetwk.h
WNNC_NET_MSNET = 65536
WNNC_NET_LANMAN = 131072
WNNC_NET_NETWARE = 196608
WNNC_NET_VINES = 262144
WNNC_NET_10NET = 327680
WNNC_NET_LOCUS = 393216
WNNC_NET_SUN_PC_NFS = 458752
WNNC_NET_LANSTEP = 524288
WNNC_NET_9TILES = 589824
WNNC_NET_LANTASTIC = 655360
WNNC_NET_AS400 = 720896
WNNC_NET_FTP_NFS = 786432
WNNC_NET_PATHWORKS = 851968
WNNC_NET_LIFENET = 917504
WNNC_NET_POWERLAN = 983040
WNNC_NET_BWNFS = 1048576
WNNC_NET_COGENT = 1114112
WNNC_NET_FARALLON = 1179648
WNNC_NET_APPLETALK = 1245184
WNNC_NET_INTERGRAPH = 1310720
WNNC_NET_SYMFONET = 1376256
WNNC_NET_CLEARCASE = 1441792
WNNC_NET_FRONTIER = 1507328
WNNC_NET_BMC = 1572864
WNNC_NET_DCE = 1638400
WNNC_NET_DECORB = 2097152
WNNC_NET_PROTSTOR = 2162688
WNNC_NET_FJ_REDIR = 2228224
WNNC_NET_DISTINCT = 2293760
WNNC_NET_TWINS = 2359296
WNNC_NET_RDR2SAMPLE = 2424832
RESOURCE_CONNECTED = 1
RESOURCE_GLOBALNET = 2
RESOURCE_REMEMBERED = 3
RESOURCE_RECENT = 4
RESOURCE_CONTEXT = 5
RESOURCETYPE_ANY = 0
RESOURCETYPE_DISK = 1
RESOURCETYPE_PRINT = 2
RESOURCETYPE_RESERVED = 8
RESOURCETYPE_UNKNOWN = -1
RESOURCEUSAGE_CONNECTABLE = 1
RESOURCEUSAGE_CONTAINER = 2
RESOURCEUSAGE_NOLOCALDEVICE = 4
RESOURCEUSAGE_SIBLING = 8
RESOURCEUSAGE_ATTACHED = 16
RESOURCEUSAGE_ALL = (RESOURCEUSAGE_CONNECTABLE | RESOURCEUSAGE_CONTAINER | RESOURCEUSAGE_ATTACHED)
RESOURCEUSAGE_RESERVED = -2147483648
RESOURCEDISPLAYTYPE_GENERIC = 0
RESOURCEDISPLAYTYPE_DOMAIN = 1
RESOURCEDISPLAYTYPE_SERVER = 2
RESOURCEDISPLAYTYPE_SHARE = 3
RESOURCEDISPLAYTYPE_FILE = 4
RESOURCEDISPLAYTYPE_GROUP = 5
RESOURCEDISPLAYTYPE_NETWORK = 6
RESOURCEDISPLAYTYPE_ROOT = 7
RESOURCEDISPLAYTYPE_SHAREADMIN = 8
RESOURCEDISPLAYTYPE_DIRECTORY = 9
RESOURCEDISPLAYTYPE_TREE = 10
RESOURCEDISPLAYTYPE_NDSCONTAINER = 11
NETPROPERTY_PERSISTENT = 1
CONNECT_UPDATE_PROFILE = 1
CONNECT_UPDATE_RECENT = 2
CONNECT_TEMPORARY = 4
CONNECT_INTERACTIVE = 8
CONNECT_PROMPT = 16
CONNECT_NEED_DRIVE = 32
CONNECT_REFCOUNT = 64
CONNECT_REDIRECT = 128
CONNECT_LOCALDRIVE = 256
CONNECT_CURRENT_MEDIA = 512
CONNECT_DEFERRED = 1024
CONNECT_RESERVED = -16777216
CONNDLG_RO_PATH = 1
CONNDLG_CONN_POINT = 2
CONNDLG_USE_MRU = 4
CONNDLG_HIDE_BOX = 8
CONNDLG_PERSIST = 16
CONNDLG_NOT_PERSIST = 32
DISC_UPDATE_PROFILE = 1
DISC_NO_FORCE = 64
UNIVERSAL_NAME_INFO_LEVEL = 1
REMOTE_NAME_INFO_LEVEL = 2
WNFMT_MULTILINE = 1
WNFMT_ABBREVIATED = 2
WNFMT_INENUM = 16
WNFMT_CONNECTION = 32
NETINFO_DLL16 = 1
NETINFO_DISKRED = 4
NETINFO_PRINTERRED = 8
RP_LOGON = 1
RP_INIFILE = 2
PP_DISPLAYERRORS = 1
WNCON_FORNETCARD = 1
WNCON_NOTROUTED = 2
WNCON_SLOWLINK = 4
WNCON_DYNAMIC = 8

## NETSETUP_NAME_TYPE, used with NetValidateName
NetSetupUnknown = 0
NetSetupMachine = 1
NetSetupWorkgroup = 2
NetSetupDomain = 3
NetSetupNonExistentDomain = 4
NetSetupDnsMachine = 5

## NETSETUP_JOIN_STATUS, use with NetGetJoinInformation
NetSetupUnknownStatus = 0
NetSetupUnjoined = 1
NetSetupWorkgroupName = 2
NetSetupDomainName = 3

NetValidateAuthentication = 1
NetValidatePasswordChange = 2
NetValidatePasswordReset = 3
