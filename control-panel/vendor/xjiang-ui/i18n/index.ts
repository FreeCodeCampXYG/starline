import { createI18n } from "vue-i18n";

import zhCN from "./locale/zh-CN.json";
import enUS from "./locale/en-US.json";

const i18n = createI18n({
  legacy: false,
  locale: "zh-CN",
  fallbackLocale: "zh-CN",
  messages: {
    "zh-CN": zhCN,
    "en-US": enUS,
  },
});

export default i18n;
