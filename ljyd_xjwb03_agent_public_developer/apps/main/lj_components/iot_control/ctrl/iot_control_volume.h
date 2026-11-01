#ifndef IOT_CONTROL_VOLUME_H
#define IOT_CONTROL_VOLUME_H

#include "qm_spec_api.h"

#ifdef __cplusplus
extern "C" {
#endif

#define IOT_CONTROL_VOLUME_SIID      2
#define IOT_CONTROL_VOLUME_PIID      1 /* 绝对音量 10..100 */
#define IOT_CONTROL_VOLUME_PIID_ADJ  2 /* 1增大 2减小 3最大 4最小 */

/* 由 iot_control 表调用。 */
int iot_control_volume_set_value(qm_spec_property_t *property);
int iot_control_volume_set_adjust(qm_spec_property_t *property);
int iot_control_volume_set_local(int volume);
#if defined(CONFIG_QM_CLI_SUPPORT) && CONFIG_QM_CLI_SUPPORT
int iot_control_volume_cli_register(void);
#endif

#ifdef __cplusplus
}
#endif

#endif
