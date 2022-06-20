/* **************************************************************** *

	dcamapi4.h:	Jun 18, 2021

	Copyright (C) 2011 - 2021 Hamamatsu Photonics K.K.. All right reserved.

 * **************************************************************** */

#ifndef _INCLUDE_DCAMAPI4_H_

#pragma pack(8)

#ifndef DCAMAPI_VER
#define	DCAMAPI_VER		4000
#endif

/* **************************************************************** *

	language absorber

 * **************************************************************** */

#ifdef __cplusplus

/* C++ */

#define	DCAM_DECLARE_BEGIN( kind, tag )	kind tag
#define	DCAM_DECLARE_END( tag )		;

#define	DCAM_DEFAULT_ARG				= 0
#define	DCAMINIT_DEFAULT_ARG			= DCAMINIT_DEFAULT

extern "C" {

#else

/* C */

#define	DCAM_DECLARE_BEGIN( kind, tag )	typedef kind
#define	DCAM_DECLARE_END( tag )		tag;

#define	DCAM_DEFAULT_ARG
#define	DCAMINIT_DEFAULT_ARG

#endif

/* **************************************************************** *

	defines

 * **************************************************************** */

/* define - HDCAM */

typedef struct tag_dcam* HDCAM;

/* define - DCAMAPI */

#ifndef DCAMAPI
#ifdef PASCAL
#define	DCAMAPI	PASCAL	/* DCAM-API based on PASCAL calling */
#else
#define DCAMAPI
#endif
#endif /* DCAMAPI */

/* define - int32 & _ui32 */

#if defined(_WIN32) || defined(WIN32) || defined(_INC_WINDOWS)
typedef	long			int32;
typedef	unsigned long	_ui32;
#else
typedef	int				int32;
typedef	unsigned int	_ui32;
#endif

/* **************************************************************** *

	constant declaration

 * **************************************************************** */

/*** --- values --- ***/

#define	DCAMCONST_FRAMESTAMP_MISMATCH	0xFFFFFFFF

/*** --- errors --- ***/

DCAM_DECLARE_BEGIN( enum, DCAMERR )
{
	/* status error */
	DCAMERR_BUSY				= 0x80000101,/*		API cannot process in busy state.		*/
	DCAMERR_NOTREADY			= 0x80000103,/*		API requires ready state.				*/
	DCAMERR_NOTSTABLE			= 0x80000104,/*		API requires stable or unstable state.	*/
	DCAMERR_UNSTABLE			= 0x80000105,/*		API does not support in unstable state.	*/
	DCAMERR_NOTBUSY				= 0x80000107,/*		API requires busy state.				*/

	DCAMERR_EXCLUDED			= 0x80000110,/*		some resource is exclusive and already used	*/

	DCAMERR_COOLINGTROUBLE		= 0x80000302,/*		something happens near cooler	*/
	DCAMERR_NOTRIGGER			= 0x80000303,/*		no trigger when necessary. Some camera supports this error.	*/
	DCAMERR_TEMPERATURE_TROUBLE = 0x80000304,/*		camera warns its temperature	*/
	DCAMERR_TOOFREQUENTTRIGGER	= 0x80000305,/*		input too frequent trigger. Some camera supports this error.	*/

	/* wait error */
	DCAMERR_ABORT				= 0x80000102,/*		abort process			*/
	DCAMERR_TIMEOUT				= 0x80000106,/*		timeout					*/
	DCAMERR_LOSTFRAME			= 0x80000301,/*		frame data is lost		*/
	DCAMERR_MISSINGFRAME_TROUBLE= 0x80000f06,/*		frame is lost but reason is low lever driver's bug	*/
	DCAMERR_INVALIDIMAGE		= 0x80000321,/*		hpk format data is invalid data	*/

	/* initialization error */
	DCAMERR_NORESOURCE			= 0x80000201,/*		not enough resource except memory	*/
	DCAMERR_NOMEMORY			= 0x80000203,/*		not enough memory		*/
	DCAMERR_NOMODULE			= 0x80000204,/*		no sub module			*/
	DCAMERR_NODRIVER			= 0x80000205,/*		no driver				*/
	DCAMERR_NOCAMERA			= 0x80000206,/*		no camera				*/
	DCAMERR_NOGRABBER			= 0x80000207,/*		no grabber				*/
	DCAMERR_NOCOMBINATION		= 0x80000208,/*		no combination on registry	*/

	DCAMERR_FAILOPEN			= 0x80001001,/* DEPRECATED */
	DCAMERR_FRAMEGRABBER_NEEDS_FIRMWAREUPDATE = 0x80001002,/*	need to update frame grabber firmware to use the camera	*/
	DCAMERR_INVALIDMODULE		= 0x80000211,/*		dcam_init() found invalid module	*/
	DCAMERR_INVALIDCOMMPORT		= 0x80000212,/*		invalid serial port		*/
	DCAMERR_FAILOPENBUS			= 0x81001001,/*		the bus or driver are not available	*/
	DCAMERR_FAILOPENCAMERA		= 0x82001001,/*		 camera report error during opening	*/
	DCAMERR_DEVICEPROBLEM		= 0x82001002,/*		initialization failed(for maico)	*/

	/* calling error */
	DCAMERR_INVALIDCAMERA		= 0x80000806,/*		invalid camera			*/
	DCAMERR_INVALIDHANDLE		= 0x80000807,/*		invalid camera handle	*/
	DCAMERR_INVALIDPARAM		= 0x80000808,/*		invalid parameter		*/
	DCAMERR_INVALIDVALUE		= 0x80000821,/*		invalid property value	*/
	DCAMERR_OUTOFRANGE			= 0x80000822,/*		value is out of range	*/
	DCAMERR_NOTWRITABLE			= 0x80000823,/*		the property is not writable	*/
	DCAMERR_NOTREADABLE			= 0x80000824,/*		the property is not readable	*/
	DCAMERR_INVALIDPROPERTYID	= 0x80000825,/*		the property id is invalid	*/
	DCAMERR_NEWAPIREQUIRED		= 0x80000826,/*		old API cannot present the value because only new API need to be used	*/
	DCAMERR_WRONGHANDSHAKE		= 0x80000827,/*		this error happens DCAM get error code from camera unexpectedly	*/
	DCAMERR_NOPROPERTY			= 0x80000828,/*		there is no altenative or influence id, or no more property id	*/
	DCAMERR_INVALIDCHANNEL		= 0x80000829,/*		the property id specifies channel but channel is invalid	*/
	DCAMERR_INVALIDVIEW			= 0x8000082a,/*		the property id specifies channel but channel is invalid	*/
	DCAMERR_INVALIDSUBARRAY		= 0x8000082b,/*		the combination of subarray values are invalid. e.g. DCAM_IDPROP_SUBARRAYHPOS + DCAM_IDPROP_SUBARRAYHSIZE is greater than the number of horizontal pixel of sensor.	*/
	DCAMERR_ACCESSDENY			= 0x8000082c,/*		the property cannot access during this DCAM STATUS	*/
	DCAMERR_NOVALUETEXT			= 0x8000082d,/*		the property does not have value text	*/
	DCAMERR_WRONGPROPERTYVALUE	= 0x8000082e,/*		at least one property value is wrong	*/
	DCAMERR_DISHARMONY			= 0x80000830,/*		the paired camera does not have same parameter	*/
	DCAMERR_FRAMEBUNDLESHOULDBEOFF=0x80000832,/*	framebundle mode should be OFF under current property settings	*/
	DCAMERR_INVALIDFRAMEINDEX	= 0x80000833,/*		the frame index is invalid	*/
	DCAMERR_INVALIDSESSIONINDEX	= 0x80000834,/*		the session index is invalid	*/
	DCAMERR_NOCORRECTIONDATA	= 0x80000838,/*		not take the dark and shading correction data yet.	*/
	DCAMERR_CHANNELDEPENDENTVALUE= 0x80000839,/*	each channel has own property value so can't return overall property value.	*/
	DCAMERR_VIEWDEPENDENTVALUE	= 0x8000083a,/*		each view has own property value so can't return overall property value.	*/
	DCAMERR_NODEVICEBUFFER	= 0x8000083b,/*		the frame count is larger than device momory size on using device memory.	*/
	DCAMERR_REQUIREDSNAP	= 0x8000083c,/*		the capture mode is sequence on using device memory.	*/
	DCAMERR_LESSSYSTEMMEMORY	= 0x8000083f,/*		the sysmte memory size is too small. PC doesn't have enough memory or is limited memory by 32bit OS.	*/

	DCAMERR_NOTSUPPORT			= 0x80000f03,/*		camera does not support the function or property with current settings	*/

	/* camera or bus trouble */
	DCAMERR_FAILREADCAMERA		= 0x83001002,/*		failed to read data from camera	*/
	DCAMERR_FAILWRITECAMERA		= 0x83001003,/*		failed to write data to the camera	*/
	DCAMERR_CONFLICTCOMMPORT	= 0x83001004,/*		conflict the com port name user set	*/
	DCAMERR_OPTICS_UNPLUGGED	= 0x83001005,/* 	Optics part is unplugged so please check it.	*/
	DCAMERR_FAILCALIBRATION		= 0x83001006,/*		fail calibration	*/

	DCAMERR_MISMATCH_CONFIGURATION= 0x83001011,/*	mismatch between camera output(connection) and frame grabber specs */

	/* 0x84000100 - 0x840001FF, DCAMERR_INVALIDMEMBER_x */
	DCAMERR_INVALIDMEMBER_3		= 0x84000103,/*		3th member variable is invalid value	*/
	DCAMERR_INVALIDMEMBER_5		= 0x84000105,/*		5th member variable is invalid value	*/
	DCAMERR_INVALIDMEMBER_7		= 0x84000107,/*		7th member variable is invalid value	*/
	DCAMERR_INVALIDMEMBER_8		= 0x84000108,/*		7th member variable is invalid value	*/
	DCAMERR_INVALIDMEMBER_9		= 0x84000109,/*		9th member variable is invalid value	*/
	DCAMERR_FAILEDOPENRECFILE	= 0x84001001,/*		DCAMREC failed to open the file	*/
	DCAMERR_INVALIDRECHANDLE	= 0x84001002,/*		DCAMREC is invalid handle	*/
	DCAMERR_FAILEDWRITEDATA		= 0x84001003,/*		DCAMREC failed to write the data	*/
	DCAMERR_FAILEDREADDATA		= 0x84001004,/*		DCAMREC failed to read the data	*/
	DCAMERR_NOWRECORDING		= 0x84001005,/*		DCAMREC is recording data now	*/
	DCAMERR_WRITEFULL			= 0x84001006,/*		DCAMREC writes full frame of the session	*/
	DCAMERR_ALREADYOCCUPIED		= 0x84001007,/*		DCAMREC handle is already occupied by other HDCAM	*/
	DCAMERR_TOOLARGEUSERDATASIZE= 0x84001008,/*		DCAMREC is set the large value to user data size	*/
	DCAMERR_INVALIDWAITHANDLE	= 0x84002001,/*		DCAMWAIT is invalid handle	*/
	DCAMERR_NEWRUNTIMEREQUIRED	= 0x84002002,/*		DCAM Module Version is older than the version that the camera requests	*/
	DCAMERR_VERSIONMISMATCH		= 0x84002003,/*		Camre returns the error on setting parameter to limit version	*/
	DCAMERR_RUNAS_FACTORYMODE	= 0x84002004,/*		Camera is running as a factory mode	*/
	DCAMERR_IMAGE_UNKNOWNSIGNATURE	= 0x84003001,/*	sigunature of image header is unknown or corrupted	*/
	DCAMERR_IMAGE_NEWRUNTIMEREQUIRED= 0x84003002,/* version of image header is newer than version that used DCAM supports	*/
	DCAMERR_IMAGE_ERRORSTATUSEXIST	= 0x84003003,/*	image header stands error status	*/
	DCAMERR_IMAGE_HEADERCORRUPTED	= 0x84004004,/*	image header value is strange	*/
	DCAMERR_IMAGE_BROKENCONTENT		= 0x84004005,/*	image content is corrupted	*/

	/* calling error for DCAM-API 2.1.3 */
	DCAMERR_UNKNOWNMSGID		= 0x80000801,/*		unknown message id		*/
	DCAMERR_UNKNOWNSTRID		= 0x80000802,/*		unknown string id		*/
	DCAMERR_UNKNOWNPARAMID		= 0x80000803,/*		unkown parameter id		*/
	DCAMERR_UNKNOWNBITSTYPE		= 0x80000804,/*		unknown bitmap bits type			*/
	DCAMERR_UNKNOWNDATATYPE		= 0x80000805,/*		unknown frame data type				*/

	/* internal error */
	DCAMERR_NONE				= 0,		/*		no error, nothing to have done		*/
	DCAMERR_INSTALLATIONINPROGRESS=0x80000f00,/*	installation progress				*/
	DCAMERR_UNREACH				= 0x80000f01,/*		internal error						*/
	DCAMERR_UNLOADED			= 0x80000f04,/*		calling after process terminated	*/
	DCAMERR_THRUADAPTER			= 0x80000f05,/*											*/
	DCAMERR_NOCONNECTION		= 0x80000f07,/*		HDCAM lost connection to camera		*/

	DCAMERR_NOTIMPLEMENT		= 0x80000f02,/*		not yet implementation				*/

	DCAMERR_DELAYEDFRAME = 0x80000f09,/*	the frame waiting re-load from hardware buffer with SNAPSHOT of DEVICEBUFFER MODE */

	DCAMERR_DEVICEINITIALIZING	= 0xb0000001,

	DCAMERR_APIINIT_INITOPTIONBYTES	= 0xa4010003,/*	DCAMAPI_INIT::initoptionbytes is invalid	*/
	DCAMERR_APIINIT_INITOPTION		= 0xa4010004,/*	DCAMAPI_INIT::initoption is invalid	*/

	DCAMERR_INITOPTION_COLLISION_BASE=0xa401C000,
	DCAMERR_INITOPTION_COLLISION_MAX= 0xa401FFFF,

	/* Between DCAMERR_INITOPTION_COLLISION_BASE and DCAMERR_INITOPTION_COLLISION_MAX means there is collision with initoption in DCAMAPI_INIT. */
	/* The value "(error code) - DCAMERR_INITOPTION_COLLISION_BASE" indicates the index which second INITOPTION group happens. */

	DCAMERR_MISSPROP_TRIGGERSOURCE	= 0xE0100110,/*		the trigger mode is internal or syncreadout on using device memory. */

	/* success */
	DCAMERR_SUCCESS				= 1			/*		no error, general success code, app should check the value is positive	*/
}
DCAM_DECLARE_END( DCAMERR )

DCAM_DECLARE_BEGIN( enum, DCAMBUF_FRAME_OPTION )
{
	DCAMBUF_FRAME_OPTION__VIEW_ALL		= 0x00000000,
	DCAMBUF_FRAME_OPTION__VIEW_1		= 0x00100000,
	DCAMBUF_FRAME_OPTION__VIEW_2		= 0x00200000,
	DCAMBUF_FRAME_OPTION__VIEW_3		= 0x00300000,
	DCAMBUF_FRAME_OPTION__VIEW_4		= 0x00400000,

	DCAMBUF_FRAME_OPTION__PROC_HIGHCONTRAST	= 0x00000010,

	DCAMBUF_FRAME_OPTION__VIEW__STEP	= 0x00100000,
	DCAMBUF_FRAME_OPTION__VIEW__MASK	= 0x00F00000,
	DCAMBUF_FRAME_OPTION__PROC__MASK	= 0x00000FF0,

	end_of_dcambuf_frame_option
}
DCAM_DECLARE_END( DCAMBUF_FRAME_OPTION )

DCAM_DECLARE_BEGIN( enum, DCAMREC_FRAME_OPTION )
{
	DCAMREC_FRAME_OPTION__VIEW_CURRENT	= 0x00000000,
	DCAMREC_FRAME_OPTION__VIEW_1		= 0x00100000,
	DCAMREC_FRAME_OPTION__VIEW_2		= 0x00200000,
	DCAMREC_FRAME_OPTION__VIEW_3		= 0x00300000,
	DCAMREC_FRAME_OPTION__VIEW_4		= 0x00400000,

	DCAMREC_FRAME_OPTION__PROC_HIGHCONTRAST	= 0x00000010,

	DCAMREC_FRAME_OPTION__VIEW__STEP	= 0x00100000,
	DCAMREC_FRAME_OPTION__VIEW__MASK	= 0x00F00000,
	DCAMREC_FRAME_OPTION__PROC__MASK	= 0x00000FF0,

	endof_dcamrec_frame_option
}
DCAM_DECLARE_END( DCAMREC_FRAME_OPTION )

DCAM_DECLARE_BEGIN( enum, DCAMBUF_METADATAOPTION )
{
	DCAMBUF_METADATAOPTION__VIEW_ALL	= DCAMBUF_FRAME_OPTION__VIEW_ALL,
	DCAMBUF_METADATAOPTION__VIEW_1		= DCAMBUF_FRAME_OPTION__VIEW_1,
	DCAMBUF_METADATAOPTION__VIEW_2		= DCAMBUF_FRAME_OPTION__VIEW_2,
	DCAMBUF_METADATAOPTION__VIEW_3		= DCAMBUF_FRAME_OPTION__VIEW_3,
	DCAMBUF_METADATAOPTION__VIEW_4		= DCAMBUF_FRAME_OPTION__VIEW_4,
	DCAMBUF_METADATAOPTION__VIEW__STEP	= DCAMBUF_FRAME_OPTION__VIEW__STEP,
	DCAMBUF_METADATAOPTION__VIEW__MASK	= DCAMBUF_FRAME_OPTION__VIEW__MASK
}
DCAM_DECLARE_END( DCAMBUF_METADATAOPTION )

DCAM_DECLARE_BEGIN( enum, DCAMREC_METADATAOPTION )
{
	DCAMREC_METADATAOPTION__LOCATION_FRAME	= 0x00000000,
	DCAMREC_METADATAOPTION__LOCATION_FILE	= 0x01000000,
	DCAMREC_METADATAOPTION__LOCATION_SESSION= 0x02000000,
	DCAMREC_METADATAOPTION__LOCATION__MASK	= 0xFF000000
}
DCAM_DECLARE_END( DCAMREC_METADATAOPTION )

DCAM_DECLARE_BEGIN( enum, DCAM_PIXELTYPE )
{
	DCAM_PIXELTYPE_MONO8		= 0x00000001,
	DCAM_PIXELTYPE_MONO16		= 0x00000002,
	DCAM_PIXELTYPE_MONO12		= 0x00000003,
	DCAM_PIXELTYPE_MONO12P		= 0x00000005,

	DCAM_PIXELTYPE_RGB24		= 0x00000021,
	DCAM_PIXELTYPE_RGB48		= 0x00000022,
	DCAM_PIXELTYPE_BGR24		= 0x00000029,
	DCAM_PIXELTYPE_BGR48		= 0x0000002a,

	DCAM_PIXELTYPE_NONE			= 0x00000000
}
DCAM_DECLARE_END( DCAM_PIXELTYPE )

DCAM_DECLARE_BEGIN( enum, DCAMBUF_ATTACHKIND )
{
	DCAMBUF_ATTACHKIND_TIMESTAMP	= 1,
	DCAMBUF_ATTACHKIND_FRAMESTAMP	= 2,

	DCAMBUF_ATTACHKIND_PRIMARY_TIMESTAMP	= 3,
	DCAMBUF_ATTACHKIND_PRIMARY_FRAMESTAMP	= 4,

	DCAMBUF_ATTACHKIND_FRAME		= 0
}
DCAM_DECLARE_END( DCAM_ATTACHKIND )

DCAM_DECLARE_BEGIN( enum, DCAMCAP_TRANSFERKIND )
{
	DCAMCAP_TRANSFERKIND_FRAME		= 0
}
DCAM_DECLARE_END( DCAMCAP_TRANSFERKIND )

/*** --- status --- ***/
DCAM_DECLARE_BEGIN( enum, DCAMCAP_STATUS )
{
	DCAMCAP_STATUS_ERROR				= 0x0000,
	DCAMCAP_STATUS_BUSY					= 0x0001,
	DCAMCAP_STATUS_READY				= 0x0002,
	DCAMCAP_STATUS_STABLE				= 0x0003,
	DCAMCAP_STATUS_UNSTABLE				= 0x0004,

	end_of_dcamcap_status
}
DCAM_DECLARE_END( DCAMCAP_STATUS )

DCAM_DECLARE_BEGIN( enum, DCAMWAIT_EVENT )
{
	DCAMWAIT_CAPEVENT_TRANSFERRED		= 0x0001,
	DCAMWAIT_CAPEVENT_FRAMEREADY		= 0x0002,	/* all modules support	*/
	DCAMWAIT_CAPEVENT_CYCLEEND			= 0x0004,	/* all modules support	*/
	DCAMWAIT_CAPEVENT_EXPOSUREEND		= 0x0008,
	DCAMWAIT_CAPEVENT_STOPPED			= 0x0010,
	DCAMWAIT_CAPEVENT_RELOADFRAME		= 0x0020,

	DCAMWAIT_RECEVENT_STOPPED			= 0x0100,
	DCAMWAIT_RECEVENT_WARNING			= 0x0200,
	DCAMWAIT_RECEVENT_MISSED			= 0x0400,
	DCAMWAIT_RECEVENT_DISKFULL			= 0x1000,
	DCAMWAIT_RECEVENT_WRITEFAULT		= 0x2000,
	DCAMWAIT_RECEVENT_SKIPPED			= 0x4000,
	DCAMWAIT_RECEVENT_WRITEFRAME		= 0x8000,	/* DCAMCAP_START_BUFRECORD only */

	end_of_dcamwait_event
}
DCAM_DECLARE_END( DCAMWAIT_EVENT )

/*** --- dcamcap_start --- ***/
DCAM_DECLARE_BEGIN( enum, DCAMCAP_START )
{
	DCAMCAP_START_SEQUENCE				= -1,
	DCAMCAP_START_SNAP					= 0
}
DCAM_DECLARE_END( DCAMCAP_START )

/*** --- string id --- ***/
DCAM_DECLARE_BEGIN( enum, DCAM_IDSTR )
{

	DCAM_IDSTR_BUS						= 0x04000101,
	DCAM_IDSTR_CAMERAID					= 0x04000102,
	DCAM_IDSTR_VENDOR					= 0x04000103,
	DCAM_IDSTR_MODEL					= 0x04000104,
	DCAM_IDSTR_CAMERAVERSION			= 0x04000105,
	DCAM_IDSTR_DRIVERVERSION			= 0x04000106,
	DCAM_IDSTR_MODULEVERSION			= 0x04000107,
	DCAM_IDSTR_DCAMAPIVERSION			= 0x04000108,
	DCAM_IDSTR_SUBUNIT_INFO1			= 0x04000110,
	DCAM_IDSTR_SUBUNIT_INFO2			= 0x04000111,
	DCAM_IDSTR_SUBUNIT_INFO3			= 0x04000112,
	DCAM_IDSTR_SUBUNIT_INFO4			= 0x04000113,

	DCAM_IDSTR_CAMERA_SERIESNAME		= 0x0400012c,

	DCAM_IDSTR_OPTICALBLOCK_MODEL		= 0x04001101,
	DCAM_IDSTR_OPTICALBLOCK_ID			= 0x04001102,
	DCAM_IDSTR_OPTICALBLOCK_DESCRIPTION	= 0x04001103,
	DCAM_IDSTR_OPTICALBLOCK_CHANNEL_1	= 0x04001104,
	DCAM_IDSTR_OPTICALBLOCK_CHANNEL_2	= 0x04001105
}
DCAM_DECLARE_END( DCAM_IDSTR )

/*** --- wait timeout --- ***/
DCAM_DECLARE_BEGIN( enum, DCAMWAIT_TIMEOUT )
{
	DCAMWAIT_TIMEOUT_INFINITE			= 0x80000000,

	end_of_dcamwait_timeout
}
DCAM_DECLARE_END( DCAMWAIT_TIMEOUT  )

#if DCAMAPI_VER >= 4000

/*** --- initialize parameter --- ***/
DCAM_DECLARE_BEGIN( enum, DCAMAPI_INITOPTION )
{
	DCAMAPI_INITOPTION_APIVER__LATEST		= 0x00000001,
	DCAMAPI_INITOPTION_APIVER__4_0			= 0x00000400,
	DCAMAPI_INITOPTION_MULTIVIEW__DISABLE	= 0x00010002,
	DCAMAPI_INITOPTION_ENDMARK				= 0x00000000
}
DCAM_DECLARE_END( DCAMAPI_INITOPTION )

/*** --- meta data kind --- ***/

DCAM_DECLARE_BEGIN( enum, DCAMBUF_METADATAKIND )
{
	DCAMBUF_METADATAKIND_TIMESTAMPS			= 0x00010000,
	DCAMBUF_METADATAKIND_FRAMESTAMPS		= 0x00020000,

	end_of_dcambuf_metadatakind
}
DCAM_DECLARE_END( DCAMBUF_METADATAKIND )

DCAM_DECLARE_BEGIN( enum, DCAMREC_METADATAKIND )
{
	DCAMREC_METADATAKIND_USERDATATEXT		= 0x00000001,
	DCAMREC_METADATAKIND_USERDATABIN		= 0x00000002,
	DCAMREC_METADATAKIND_TIMESTAMPS			= 0x00010000,
	DCAMREC_METADATAKIND_FRAMESTAMPS		= 0x00020000,

	end_of_dcamrec_metadatakind
}
DCAM_DECLARE_END( DCAMREC_METADATAKIND )

/*** --- DCAM data option --- ***/

DCAM_DECLARE_BEGIN( enum, DCAMDATA_OPTION )
{
	DCAMDATA_OPTION__VIEW_ALL				= DCAMBUF_FRAME_OPTION__VIEW_ALL,
	DCAMDATA_OPTION__VIEW_1					= DCAMBUF_FRAME_OPTION__VIEW_1,
	DCAMDATA_OPTION__VIEW_2					= DCAMBUF_FRAME_OPTION__VIEW_2,
	DCAMDATA_OPTION__VIEW_3					= DCAMBUF_FRAME_OPTION__VIEW_3,
	DCAMDATA_OPTION__VIEW_4					= DCAMBUF_FRAME_OPTION__VIEW_4,

	DCAMDATA_OPTION__VIEW__STEP				= DCAMBUF_FRAME_OPTION__VIEW__STEP,
	DCAMDATA_OPTION__VIEW__MASK				= DCAMBUF_FRAME_OPTION__VIEW__MASK,
}
DCAM_DECLARE_END( DCAMDATA_OPTION )

/*** --- DCAM data kind --- ***/

DCAM_DECLARE_BEGIN( enum, DCAMDATA_KIND )
{
	DCAMDATA_KIND__REGION					= 0x00000001,
	DCAMDATA_KIND__LUT						= 0x00000002,
	DCAMDATA_KIND__NONE						= 0x00000000
}
DCAM_DECLARE_END( DCAMDATA_KIND )

/*** --- DCAM data attribute --- ***/
DCAM_DECLARE_BEGIN( enum, DCAMDATA_ATTRIBUTE )
{
	DCAMDATA_ATTRIBUTE__ACCESSREADY			= 0x01000000,	/* This value can get or set at READY status */
	DCAMDATA_ATTRIBUTE__ACCESSBUSY			= 0x02000000,	/* This value can get or set at BUSY status */

	DCAMDATA_ATTRIBUTE__HASVIEW				= 0x10000000,	/* value can set the value for each views	*/

	DCAMDATA_ATTRIBUTE__MASK				= 0xFF000000,
}
DCAM_DECLARE_END( DCAMDATA_ATTRIBUTE )

/*** --- DCAM data region type --- ***/
DCAM_DECLARE_BEGIN( enum, DCAMDATA_REGIONTYPE )
{
	DCAMDATA_REGIONTYPE__BYTEMASK			= 0x00000001,
	DCAMDATA_REGIONTYPE__RECT16ARRAY		= 0x00000002,

	DCAMDATA_REGIONTYPE__ACCESSREADY		= DCAMDATA_ATTRIBUTE__ACCESSREADY,
	DCAMDATA_REGIONTYPE__ACCESSBUSY			= DCAMDATA_ATTRIBUTE__ACCESSBUSY,
	DCAMDATA_REGIONTYPE__HASVIEW			= DCAMDATA_ATTRIBUTE__HASVIEW,

	DCAMDATA_REGIONTYPE__BODYMASK			= 0x00FFFFFF,
	DCAMDATA_REGIONTYPE__ATTRIBUTEMASK		= DCAMDATA_ATTRIBUTE__MASK,

	DCAMDATA_REGIONTYPE__NONE				= 0x00000000
}
DCAM_DECLARE_END( DCAMDATA_REGIONTYPE )

/*** --- DCAM data lut type --- ***/
DCAM_DECLARE_BEGIN( enum, DCAMDATA_LUTTYPE )
{
	DCAMDATA_LUTTYPE__SEGMENTED_LINEAR		= 0x00000001,
	DCAMDATA_LUTTYPE__MONO16				= 0x00000002,	// reserved

	DCAMDATA_LUTTYPE__ACCESSREADY			= DCAMDATA_ATTRIBUTE__ACCESSREADY,
	DCAMDATA_LUTTYPE__ACCESSBUSY			= DCAMDATA_ATTRIBUTE__ACCESSBUSY,

	DCAMDATA_LUTTYPE__BODYMASK				= 0x00FFFFFF,
	DCAMDATA_LUTTYPE__ATTRIBUTEMASK			= DCAMDATA_ATTRIBUTE__MASK,

	DCAMDATA_LUTTYPE__NONE					= 0x00000000
}
DCAM_DECLARE_END( DCAMDATA_LUTTYPE )

/*** --- DCAMBUF proc type --- ***/
DCAM_DECLARE_BEGIN( enum, DCAMBUF_PROCTYPE )
{
	DCAMBUF_PROCTYPE__HIGHCONTRASTMODE		= DCAMBUF_FRAME_OPTION__PROC_HIGHCONTRAST,

	DCAMBUF_PROCTYPE__NONE					= 0x00000000
}
DCAM_DECLARE_END( DCAMBUF_PROCTYPE )

/*** --- Code Page --- ***/

DCAM_DECLARE_BEGIN( enum, DCAM_CODEPAGE )
{
	DCAM_CODEPAGE__SHIFT_JIS				= 932,		// Shift JIS

	DCAM_CODEPAGE__UTF16_LE					= 1200,		// UTF-16 (Little Endian)
	DCAM_CODEPAGE__UTF16_BE					= 1201,		// UTF-16 (Big Endian)

	DCAM_CODEPAGE__UTF7						= 65000,	// UTF-7 translation
	DCAM_CODEPAGE__UTF8						= 65001,	// UTF-8 translation

	DCAM_CODEPAGE__NONE						= 0x00000000
}
DCAM_DECLARE_END( DCAM_CODEPAGE )

/*** --- capability --- ***/
DCAM_DECLARE_BEGIN( enum, DCAMDEV_CAPDOMAIN )
{
	DCAMDEV_CAPDOMAIN__DCAMDATA				= 0x00000001,
	DCAMDEV_CAPDOMAIN__FRAMEOPTION			= 0x00000002,

	DCAMDEV_CAPDOMAIN__FUNCTION				= 0x00000000
}
DCAM_DECLARE_END( DCAMDEV_CAPDOMAIN )

DCAM_DECLARE_BEGIN( enum, DCAMDEV_CAPFLAG )
{
	DCAMDEV_CAPFLAG_FRAMESTAMP				= 0x00000001,
	DCAMDEV_CAPFLAG_TIMESTAMP				= 0x00000002,
	DCAMDEV_CAPFLAG_CAMERASTAMP				= 0x00000004,

	DCAMDEV_CAPFLAG_NONE					= 0x00000000
}
DCAM_DECLARE_END( DCAMDEV_CAPFLAG )
DCAM_DECLARE_BEGIN( enum, DCAMREC_STATUSFLAG )
{
	DCAMREC_STATUSFLAG_NONE					= 0x00000000,
	DCAMREC_STATUSFLAG_RECORDING			= 0x00000001,

	end_of_dcamrec_statusflag
}
DCAM_DECLARE_END( DCAMREC_STATUSFLAG )

/* **************************************************************** *

	structures (ver 4.x)

 * **************************************************************** */

typedef struct DCAMWAIT*	HDCAMWAIT;
typedef struct DCAMREC*		HDCAMREC;

DCAM_DECLARE_BEGIN( struct, DCAM_GUID )
{
	_ui32				Data1;
	unsigned short		Data2;
	unsigned short		Data3;
	unsigned char		Data4[ 8 ];
}
DCAM_DECLARE_END( DCAM_GUID )

DCAM_DECLARE_BEGIN( struct, DCAMAPI_INIT )
{
	int32				size;					// [in]
	int32				iDeviceCount;			// [out]
	int32				reserved;				// reserved
	int32				initoptionbytes;		// [in] maximum bytes of initoption array.
	const int32*		initoption;				// [in ptr] initialize options. Choose from DCAMAPI_INITOPTION
	const DCAM_GUID*	guid;					// [in ptr]
}
DCAM_DECLARE_END( DCAMAPI_INIT )

DCAM_DECLARE_BEGIN( struct, DCAMDEV_OPEN )
{
	int32				size;					// [in]
	int32				index;					// [in]
	HDCAM				hdcam;					// [out]
}
DCAM_DECLARE_END( DCAMDEV_OPEN )

DCAM_DECLARE_BEGIN( struct, DCAMDEV_CAPABILITY )
{
	int32				size;					// [in]
	int32				domain;					// [in] DCAMDEV_CAPDOMAIN__*
	int32				capflag;				// [out] available flags in current condition.
	int32				kind;					// [in] data kind in domain
}
DCAM_DECLARE_END( DCAMDEV_CAPABILITY )

DCAM_DECLARE_BEGIN( struct, DCAMDEV_CAPABILITY_LUT )
{
	DCAMDEV_CAPABILITY	hdr;					// [in] size:		size of this structure
												// [in] domain:		DCAMDEV_CAPDOMAIN__DCAMDATA
												// [out]capflag:	DCAMDATA_LUTTYPE__*
												// [in] kind:		DCAMDATA_KIND__LUT

	int32				linearpointmax;			// [out] max of linear lut point
}
DCAM_DECLARE_END( DCAMDEV_CAPABILITY_LUT )

DCAM_DECLARE_BEGIN( struct, DCAMDEV_CAPABILITY_REGION )
{
	DCAMDEV_CAPABILITY	hdr;					// [in] size:		size of this structure
												// [in]	domain:		DCAMDEV_CAPDOMAIN__DCAMDATA
												// [out]capflag:	DCAMDATA_REGIONTYPE__*
												// [in]	kind:		DCAMDATA_KIND__REGION

	int32				horzunit;				// [out] horizontal step
	int32				vertunit;				// [out] vertical step
}
DCAM_DECLARE_END( DCAMDEV_CAPABILITY_REGION )

DCAM_DECLARE_BEGIN( struct, DCAMDEV_CAPABILITY_FRAMEOPTION )
{
	DCAMDEV_CAPABILITY	hdr;					// [in] size:		size of this structure
												// [in]	domain:		DCAMDEV_CAPDOMAIN__FRAMEOPTION
												// [out]capflag:	available DCAMBUF_PROCTYPE__* flags in current condition.
												// [in]	kind:		0 reserved

	int32	supportproc;						// [out] support DCAMBUF_PROCTYPE__* flags in the camera. hdr.capflag may be 0 if the function doesn't work in current condition.
}
DCAM_DECLARE_END( DCAMDEV_CAPABILITY_FRAMEOPTION )

DCAM_DECLARE_BEGIN( struct, DCAMDEV_STRING )
{
	int32				size;					// [in]
	int32				iString;				// [in]
	char*				text;					// [in,obuf]
	int32				textbytes;				// [in]
}
DCAM_DECLARE_END( DCAMDEV_STRING )

DCAM_DECLARE_BEGIN( struct, DCAMDATA_HDR )
{
	int32				size;					// [in]	size of whole structure, not only this
	int32				iKind;					// [in] DCAMDATA_KIND__*
	int32				option;					// [in] DCAMDATA_OPTION__*
	int32				reserved2;				// [in] 0 reserved
}
DCAM_DECLARE_END( DCAMDATA_HDR )

DCAM_DECLARE_BEGIN( struct, DCAMDATA_REGION )
{
	DCAMDATA_HDR		hdr;					// [in] iKind = DCAMDATA_KIND__REGION

	int32				option;					// 0 reserved
	int32				type;					// [in] DCAMDATA_REGIONTYPE
	void*				data;					// Byte array or DCAMDATA_REGIONRECT array
	int32				datasize;				// size of data
	int32				reserved;				// 0 reserved
}
DCAM_DECLARE_END( DCAMDATA_REGION )

DCAM_DECLARE_BEGIN( struct, DCAMDATA_REGIONRECT )
{
	short	left;
	short	top;
	short	right;
	short	bottom;
}
DCAM_DECLARE_END( DCAMDATA_REGIONRECT )

DCAM_DECLARE_BEGIN( struct, DCAMDATA_LUT )
{
	DCAMDATA_HDR		hdr;					// [in] iKind = DCAMDATA_KIND__LUT

	int32				type;					// [in]	DCAMDATA_LUTTYPE
	int32				page;					// [in] use to load or store
	void*				data;					// WORD array or DCAMDATA_LINEARLUT array
	int32				datasize;				// size of data
	int32				reserved;				// 0 reserved
}
DCAM_DECLARE_END( DCAMDATA_LUT )

DCAM_DECLARE_BEGIN( struct, DCAMDATA_LINEARLUT )
{
	int32	lutin;
	int32	lutout;
}
DCAM_DECLARE_END( DCAMDATA_LINEARLUT )

DCAM_DECLARE_BEGIN( struct, DCAMPROP_ATTR )
{
	/* input parameters */
	int32				cbSize;					// [in] size of this structure
	int32				iProp;					//	DCAMIDPROPERTY
	int32				option;					//	DCAMPROPOPTION
	int32				iReserved1;				//	must be 0

	/* output parameters */
	int32				attribute;				//	DCAMPROPATTRIBUTE
	int32				iGroup;					//	0 reserved;
	int32				iUnit;					//	DCAMPROPUNIT
	int32				attribute2;				//	DCAMPROPATTRIBUTE2

	double				valuemin;				//	minimum value
	double				valuemax;				//	maximum value
	double				valuestep;				//	minimum stepping between a value and the next
	double				valuedefault;			//	default value

	int32				nMaxChannel;			//	max channel if supports
	int32				iReserved3;				//	reserved to 0
	int32				nMaxView;				//	max view if supports

	int32				iProp_NumberOfElement;	//	property id to get number of elements of this property if it is array
	int32				iProp_ArrayBase;		//	base id of array if element
	int32				iPropStep_Element;		//	step for iProp to next element
}
DCAM_DECLARE_END( DCAMPROP_ATTR )

DCAM_DECLARE_BEGIN( struct, DCAMPROP_VALUETEXT )
{
	int32				cbSize;					// [in] size of this structure
	int32				iProp;					// [in] DCAMIDPROP
	double				value;					// [in] value of property
	char*				text;					// [in,obuf] text of the value
	int32				textbytes;				// [in] text buf size
}
DCAM_DECLARE_END( DCAMPROP_VALUETEXT )

DCAM_DECLARE_BEGIN( struct, DCAMBUF_ATTACH )
{
	int32				size;					// [in] size of this structure.
	int32				iKind;					// [in] DCAMBUF_ATTACHKIND
	void**				buffer;					// [in,ptr]
	int32				buffercount;			// [in]
}
DCAM_DECLARE_END( DCAMBUF_ATTACH )

DCAM_DECLARE_BEGIN( struct, DCAM_TIMESTAMP )
{
	_ui32				sec;					// [out]
	int32				microsec;				// [out]
}
DCAM_DECLARE_END( DCAM_TIMESTAMP )

DCAM_DECLARE_BEGIN( struct, DCAMCAP_TRANSFERINFO )
{
	int32				size;					// [in] size of this structure.
	int32				iKind;					// [in] DCAMCAP_TRANSFERKIND
	int32				nNewestFrameIndex;		// [out]
	int32				nFrameCount;			// [out]
}
DCAM_DECLARE_END( DCAMCAP_TRANSFERINFO )

DCAM_DECLARE_BEGIN( struct, DCAMBUF_FRAME )
{
	// copyframe() and lockframe() use this structure. Some members have different direction.
	// [i:o] means, the member is input at copyframe() and output at lockframe().
	// [i:i] and [o:o] means always input and output at both function.
	// "input" means application has to set the value before calling.
	// "output" means function filles a value at returning.
	int32				size;					// [i:i] size of this structure.
	int32				iKind;					// reserved. set to 0.
	int32				option;					// reserved. set to 0.
	int32				iFrame;					// [i:i] frame index
	void*				buf;					// [i:o] pointer for top-left image
	int32				rowbytes;				// [i:o] byte size for next line.
	DCAM_PIXELTYPE		type;					// reserved. set to 0.
	int32				width;					// [i:o] horizontal pixel count
	int32				height;					// [i:o] vertical line count
	int32				left;					// [i:o] horizontal start pixel
	int32				top;					// [i:o] vertical start line
	DCAM_TIMESTAMP		timestamp;				// [o:o] timestamp
	int32				framestamp;				// [o:o] framestamp
	int32				camerastamp;			// [o:o] camerastamp
}
DCAM_DECLARE_END( DCAMBUF_FRAME )

DCAM_DECLARE_BEGIN( struct, DCAMREC_FRAME )	// currently the structure is same as DCAM_FRAME. option flag means are different.
{
	// copyframe() and lockframe() use this structure. Some members have different direction.
	// [i:o] means, the member is input at copyframe() and output at lockframe().
	// [i:i] and [o:o] means always input and output at both function.
	// "input" means application has to set the value before calling.
	// "output" means function filles a value at returning.
	int32				size;					// [i:i] size of this structure.
	int32				iKind;					// reserved. set to 0.
	int32				option;					// DCAMREC_FRAME_OPTION
	int32				iFrame;					// [i:i] frame index
	void*				buf;					// [i:o] pointer for top-left image
	int32				rowbytes;				// [i:o] byte size for next line.
	DCAM_PIXELTYPE		type;					// reserved. set to 0.
	int32				width;					// [i:o] horizontal pixel count
	int32				height;					// [i:o] vertical line count
	int32				left;					// [i:o] horizontal start pixel
	int32				top;					// [i:o] vertical start line
	DCAM_TIMESTAMP		timestamp;				// [o:o] timestamp
	int32				framestamp;				// [o:o] framestamp
	int32				camerastamp;			// [o:o] camerastamp
}
DCAM_DECLARE_END( DCAMREC_FRAME )

DCAM_DECLARE_BEGIN( struct, DCAMWAIT_OPEN )
{
	int32				size;					// [in] size of this structure.
	int32				supportevent;			// [out];
	HDCAMWAIT			hwait;					// [out];
	HDCAM				hdcam;					// [in];
}
DCAM_DECLARE_END( DCAMWAIT_OPEN )

DCAM_DECLARE_BEGIN( struct, DCAMWAIT_START)
{
	int32				size;					// [in] size of this structure.
	int32				eventhappened;			// [out]
	int32				eventmask;				// [in]
	int32				timeout;				// [in]
}
DCAM_DECLARE_END( DCAMWAIT_START )

#if defined(_WIN32) || defined(WIN32)

DCAM_DECLARE_BEGIN( struct, DCAMREC_OPENA )
{
	int32				size;					// [in] size of this structure.
	int32				reserved;				// [in]
	HDCAMREC			hrec;					// [out]
	const char*			path;					// [in]
	const char*			ext;					// [in]
	int32				maxframepersession;		// [in]
	int32				userdatasize;			// [in]
	int32				userdatasize_session;	// [in]
	int32				userdatasize_file;		// [in]
	int32				usertextsize;			// [in]
	int32				usertextsize_session;	// [in]
	int32				usertextsize_file;		// [in]
}
DCAM_DECLARE_END( DCAMREC_OPENA )

DCAM_DECLARE_BEGIN( struct, DCAMREC_OPENW )
{
	int32				size;					// [in] size of this structure.
	int32				reserved;				// [in]
	HDCAMREC			hrec;					// [out]
	const wchar_t*		path;					// [in]
	const wchar_t*		ext;					// [in]
	int32				maxframepersession;		// [in]
	int32				userdatasize;			// [in]
	int32				userdatasize_session;	// [in]
	int32				userdatasize_file;		// [in]
	int32				usertextsize;			// [in]
	int32				usertextsize_session;	// [in]
	int32				usertextsize_file;		// [in]
}
DCAM_DECLARE_END( DCAMREC_OPENW )

#else

DCAM_DECLARE_BEGIN( struct, DCAMREC_OPEN )
{
	int32				size;					// [in] size of this structure.
	int32				reserved;				// [in]
	HDCAMREC			hrec;					// [out]
	const char*			path;					// [in]
	const char*			ext;					// [in]
	int32				maxframepersession;		// [in]
	int32				userdatasize;			// [in]
	int32				userdatasize_session;	// [in]
	int32				userdatasize_file;		// [in]
	int32				usertextsize;			// [in]
	int32				usertextsize_session;	// [in]
	int32				usertextsize_file;		// [in]
}
DCAM_DECLARE_END( DCAMREC_OPEN )

#endif

DCAM_DECLARE_BEGIN( struct, DCAMREC_STATUS )
{
	int32				size;
	int32				currentsession_index;
	int32				maxframecount_per_session;
	int32				currentframe_index;
	int32				missingframe_count;
	int32				flags;					// DCAMREC_STATUSFLAG
	int32				totalframecount;
	int32				reserved;
}
DCAM_DECLARE_END( DCAMREC_STATUS )

DCAM_DECLARE_BEGIN( struct, DCAM_METADATAHDR )
{
	int32				size;					// [in] size of whole structure, not only this.
	int32				iKind;					// [in] DCAM_METADATAKIND
	int32				option;					// [in] value meaning depends on DCAM_METADATAKIND
	int32				iFrame;					// [in] frame index
}
DCAM_DECLARE_END( DCAM_METADATAHDR )

DCAM_DECLARE_BEGIN( struct, DCAM_METADATABLOCKHDR )
{
	int32				size;					// [in] size of whole structure, not only this.
	int32				iKind;					// [in] DCAM_METADATAKIND
	int32				option;					// [in] value meaning depends on DCAMBUF_METADATAOPTION or DCAMREC_METADATAOPTION
	int32				iFrame;					// [in] start frame index
	int32				in_count;				// [in] max count of meta data
	int32				outcount;				// [out] count of got meta data.
}
DCAM_DECLARE_END( DCAM_METADATABLOCKHDR )

DCAM_DECLARE_BEGIN( struct, DCAM_USERDATATEXT )
{
	DCAM_METADATAHDR	hdr;					// [in] size member should be size of this structure
												// [in] iKind should be DCAMREC_METADATAKIND_USERDATATEXT.
												// [in] option should be one of DCAMREC_METADATAOPTION

	char*				text;					// [in] UTF-8 encoding
	int32				text_len;				// [in] byte size of meta data.
	int32				codepage;				// [in] DCAM_CODEPAGE.
}
DCAM_DECLARE_END( DCAM_USERDATATEXT )

DCAM_DECLARE_BEGIN( struct, DCAM_USERDATABIN )
{
	DCAM_METADATAHDR	hdr;					// [in] size member should be size of this structure
												// [in] iKind should be DCAMREC_METADATAKIND_USERDATABIN.
												// [in] option should be one of DCAMREC_METADATAOPTION

	void*				bin;					// [in] binary meta data
	int32				bin_len;				// [in] byte size of binary meta data.
	int32				reserved;				// [in] 0 reserved.
}
DCAM_DECLARE_END( DCAM_USERDATABIN )

DCAM_DECLARE_BEGIN( struct, DCAM_TIMESTAMPBLOCK )
{
	DCAM_METADATABLOCKHDR	hdr;				// [in] size member should be size of this structure
												// [in] iKind should be DCAMREC_METADATAKIND_TIMESTAMPS.
												// [in] option should be one of DCAMBUF_METADATAOPTION or DCAMREC_METADATAOPTION

	DCAM_TIMESTAMP*		timestamps;				// [in] pointer for TIMESTAMP block
	int32				timestampsize;			// [in] sizeof(DCAM_TIMESTRAMP)
	int32				timestampvaildsize;		// [o] return the written data size of DCAM_TIMESTRAMP.
	int32				timestampkind;			// [o] return timestamp kind(Hardware, Driver, DCAM etc..)
	int32				reserved;
}
DCAM_DECLARE_END( DCAM_TIMESTAMPBLOCK )

DCAM_DECLARE_BEGIN( struct, DCAM_FRAMESTAMPBLOCK )
{
	DCAM_METADATABLOCKHDR	hdr;				// [in] size member should be size of this structure
												// [in] iKind should be DCAM_METADATAKIND_FRAMESTAMPS.
												// [in] option should be one of DCAMBUF_METADATAOPTION or DCAMREC_METADATAOPTION

	int32*	framestamps;						// [in] pointer for framestamp block
	int32	reserved;
}
DCAM_DECLARE_END( DCAM_FRAMESTAMPBLOCK )

DCAM_DECLARE_BEGIN( struct, DCAM_METADATATEXTBLOCK )
{
	DCAM_METADATABLOCKHDR	hdr;

	void*				text;					// [i/o] see below.
	int32*				textsizes;				// [i/o] see below.
	int32				bytesperunit;			// [i/o] see below.
	int32				reserved;				// [in] reserved to 0
	int32*				textcodepage;			// [i/o] see below.

// Note
	// dcamrec_copymetadatablock()
	//	buf										// [in] pointer for filling userdatatext block
	//	unitsizes								// [in] pointer for filling each text size of METADATA
	//	bytesperunit							// [in] max bytes per unit for filling each METADATA
	//	textcodepage							// [in] pointer for filling each text codepage of METADATA

	// dcamrec_lockmetadatablock()
	//	buf										// [out] return DCAM internal pointer of userdatatext block
	//	unitsizes								// [out] return DCAM internal array pointer of each size
	//	bytesperunit							// [out] max bytes per unit which is set at DCAMREC_OPEN
	//	textcodepage							// [out] return DCAM internal array pointer of each codepage
}
DCAM_DECLARE_END( DCAM_METADATATEXTBLOCK )

DCAM_DECLARE_BEGIN( struct, DCAM_METADATABINBLOCK )
{
	DCAM_METADATABLOCKHDR	hdr;

	void*				bin;					// [i/o] see below.
	int32*				binsizes;				// [i/o] see below.
	int32				bytesperunit;			// [i/o] see below.
	int32				reserved;				// [in] reserved to 0

// Note
	// dcamrec_copymetadatablock()
	//	bin										// [in] pointer for filling userdatabin block
	//	binsizes								// [in] pointer for filling each bin size of METADATA
	//	bytesperunit							// [in] max bytes per unit for filling each METADATA

	// dcamrec_lockmetadatablock()
	//	bin										// [out] return DCAM internal pointer of userdata bin block
	//	binsizes								// [out] return DCAM internal array pointer of each bin size
	//	bytesperunit							// [out] max bytes per unit which is set at DCAMREC_OPEN
}
DCAM_DECLARE_END( DCAM_METADATABINBLOCK )

/* **************************************************************** *

	functions (ver 4.x)

 * **************************************************************** */

// Initialize, uninitialize and misc.
DCAMERR DCAMAPI dcamapi_init			( DCAMAPI_INIT* param DCAM_DEFAULT_ARG );
DCAMERR DCAMAPI dcamapi_uninit			();
DCAMERR DCAMAPI dcamdev_open			( DCAMDEV_OPEN* param );
DCAMERR DCAMAPI dcamdev_close			( HDCAM h );
DCAMERR DCAMAPI dcamdev_showpanel		( HDCAM h, int32 iKind );
DCAMERR DCAMAPI dcamdev_getcapability	( HDCAM h, DCAMDEV_CAPABILITY* param );
DCAMERR DCAMAPI dcamdev_getstring		( HDCAM h, DCAMDEV_STRING* param );
DCAMERR DCAMAPI dcamdev_setdata			( HDCAM h, DCAMDATA_HDR* param );
DCAMERR DCAMAPI dcamdev_getdata			( HDCAM h, DCAMDATA_HDR* param );

// Property control
DCAMERR DCAMAPI dcamprop_getattr		( HDCAM h, DCAMPROP_ATTR* param );
DCAMERR DCAMAPI dcamprop_getvalue		( HDCAM h, int32 iProp, double* pValue );
DCAMERR DCAMAPI dcamprop_setvalue		( HDCAM h, int32 iProp, double  fValue );
DCAMERR DCAMAPI dcamprop_setgetvalue	( HDCAM h, int32 iProp, double* pValue, int32 option DCAM_DEFAULT_ARG );
DCAMERR DCAMAPI dcamprop_queryvalue		( HDCAM h, int32 iProp, double* pValue, int32 option DCAM_DEFAULT_ARG );
DCAMERR DCAMAPI dcamprop_getnextid		( HDCAM h, int32* pProp, int32 option DCAM_DEFAULT_ARG );
DCAMERR DCAMAPI dcamprop_getname		( HDCAM h, int32 iProp, char* text, int32 textbytes );
DCAMERR DCAMAPI dcamprop_getvaluetext	( HDCAM h, DCAMPROP_VALUETEXT* param );

// Buffer control
DCAMERR DCAMAPI dcambuf_alloc			( HDCAM h, int32 framecount );	// call dcambuf_release() to free.
DCAMERR DCAMAPI dcambuf_attach			( HDCAM h, const DCAMBUF_ATTACH* param );
DCAMERR DCAMAPI dcambuf_release			( HDCAM h, int32 iKind DCAM_DEFAULT_ARG );
DCAMERR DCAMAPI dcambuf_lockframe		( HDCAM h, DCAMBUF_FRAME* pFrame );
DCAMERR DCAMAPI dcambuf_copyframe		( HDCAM h, DCAMBUF_FRAME* pFrame );
DCAMERR DCAMAPI dcambuf_copymetadata	( HDCAM h, DCAM_METADATAHDR* hdr );

// Capturing
DCAMERR DCAMAPI dcamcap_start			( HDCAM h, int32 mode );
DCAMERR DCAMAPI dcamcap_stop			( HDCAM h );
DCAMERR DCAMAPI dcamcap_status			( HDCAM h, int32* pStatus );
DCAMERR DCAMAPI dcamcap_transferinfo	( HDCAM h, DCAMCAP_TRANSFERINFO* param );
DCAMERR DCAMAPI dcamcap_firetrigger		( HDCAM h, int32 iKind DCAM_DEFAULT_ARG );
DCAMERR DCAMAPI dcamcap_record			( HDCAM h, HDCAMREC hrec );

// Wait abort handle control
DCAMERR DCAMAPI dcamwait_open			( DCAMWAIT_OPEN* param );
DCAMERR DCAMAPI dcamwait_close			( HDCAMWAIT hWait );
DCAMERR DCAMAPI dcamwait_start			( HDCAMWAIT hWait, DCAMWAIT_START* param );
DCAMERR DCAMAPI dcamwait_abort			( HDCAMWAIT hWait );

// Recording
#if defined(_WIN32) || defined(WIN32)
DCAMERR DCAMAPI dcamrec_openA			( DCAMREC_OPENA* param );
DCAMERR DCAMAPI dcamrec_openW			( DCAMREC_OPENW* param );

#if defined(UNICODE) || defined(_UNICODE)
#define	DCAMREC_OPEN	DCAMREC_OPENW
#define	dcamrec_open	dcamrec_openW
#else
#define	DCAMREC_OPEN	DCAMREC_OPENA
#define	dcamrec_open	dcamrec_openA
#endif

#else
DCAMERR DCAMAPI dcamrec_open			( DCAMREC_OPEN* param );
#endif

DCAMERR DCAMAPI dcamrec_close			( HDCAMREC hrec );
DCAMERR DCAMAPI dcamrec_lockframe		( HDCAMREC hrec, DCAMREC_FRAME* pFrame );
DCAMERR DCAMAPI dcamrec_copyframe		( HDCAMREC hrec, DCAMREC_FRAME* pFrame );
DCAMERR DCAMAPI dcamrec_writemetadata	( HDCAMREC hrec, const DCAM_METADATAHDR* hdr );
DCAMERR DCAMAPI dcamrec_lockmetadata	( HDCAMREC hrec, DCAM_METADATAHDR* hdr );
DCAMERR DCAMAPI dcamrec_copymetadata	( HDCAMREC hrec, DCAM_METADATAHDR* hdr );
DCAMERR DCAMAPI dcamrec_lockmetadatablock( HDCAMREC hrec, DCAM_METADATABLOCKHDR* hdr );
DCAMERR DCAMAPI dcamrec_copymetadatablock( HDCAMREC hrec, DCAM_METADATABLOCKHDR* hdr );

DCAMERR DCAMAPI dcamrec_pause			( HDCAMREC hrec );
DCAMERR DCAMAPI dcamrec_resume			( HDCAMREC hrec );
DCAMERR DCAMAPI dcamrec_status			( HDCAMREC hrec, DCAMREC_STATUS* pStatus );

DCAM_DECLARE_BEGIN( struct, DCAM_METADATABLOCK )
{
	DCAM_METADATABLOCKHDR	hdr;

	void*				buf;					// [i/o] see below.
	int32*				unitsizes;				// [i/o] see below.
	int32				bytesperunit;			// [i/o] see below.
	int32				userdata_kind;			// [in] choose userdata kind(File, Session, Frame)

// Note
	// dcamrec_copymetadatablock()
	//	buf										// [in] pointer for filling userdata block
	//	unitsizes								// [in] pointer for filling each unit size of METADATA
	//	bytesperunit							// [in] max bytes per unit for filling each METADATA

	// dcamrec_lockmetadatablock()
	//	buf										// [out] return DCAM internal pointer of userdata block
	//	unitsizes								// [out] return DCAM internal array pointer of each size
	//	bytesperunit							// [out] max bytes per unit which is set at DCAMREC_OPEN
}
DCAM_DECLARE_END( DCAM_METADATABLOCK )

#endif // DCAMAPI_VER >= 4000

/* **************************************************************** */

#ifdef __cplusplus

/* end of extern "C" */
};

/*** C++ utility ***/

inline int failed( DCAMERR err )
{
	return int(err) < 0;
}

#endif

#if (defined(_MSC_VER)&&defined(_LINK_DCAMAPI_LIB))
#pragma comment(lib, "dcamapi.lib")
#endif

#pragma pack()

#define	_INCLUDE_DCAMAPI4_H_
#endif
