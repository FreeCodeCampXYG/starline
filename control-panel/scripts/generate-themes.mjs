// 0.4.0 根入口含 Node 无法解析的动态色模块；只导入本工具所需且已验证的 HCT 核心文件。
import { Hct } from "../node_modules/@material/material-color-utilities/hct/hct.js";
import { TonalPalette } from "../node_modules/@material/material-color-utilities/palettes/tonal_palette.js";
import { argbFromHex, hexFromArgb } from "../node_modules/@material/material-color-utilities/utils/string_utils.js";
import { writeFile } from "node:fs/promises";

// HCT 同一色相按感知明度生成角色，避免逐个按钮手挑颜色造成不一致。
const source = Hct.fromInt(argbFromHex("#786b88"));
const primary = TonalPalette.fromHueAndChroma(source.hue, 26);
const neutral = TonalPalette.fromHueAndChroma(75, 4);
const neutralVariant = TonalPalette.fromHueAndChroma(source.hue, 6);
const sage = TonalPalette.fromHueAndChroma(150, 19);
const oat = TonalPalette.fromHueAndChroma(65, 15);
const hex = (palette, tone) => hexFromArgb(palette.tone(tone));
function roles(dark, accent = primary) {
  const base = dark ? neutralVariant : neutral;
  return {
    "app-bg": hex(base, dark ? 9 : 97), surface: hex(base, dark ? 14 : 99),
    text: hex(neutralVariant, dark ? 93 : 17), muted: hex(neutralVariant, dark ? 76 : 38),
    accent: hex(accent, dark ? 80 : 40), "on-accent": hex(accent, dark ? 15 : 100),
    tint: hex(accent, dark ? 22 : 92), line: hex(neutralVariant, dark ? 27 : 90),
    banner: hex(base, dark ? 14 : 99),
    "art-start": hex(accent, dark ? 84 : 65), "art-end": hex(accent, dark ? 70 : 43),
    "cover-2": hex(oat, dark ? 22 : 92), "cover-3": hex(sage, dark ? 22 : 92)
  };
}
const palettes = { light: roles(false), dark: roles(true), forest: roles(false, sage) };
await writeFile(new URL("../src/themes.json", import.meta.url), JSON.stringify(palettes, null, 2) + "\n", "utf8");
console.log(JSON.stringify({source:"#786b88",model:"Material HCT semantic tonal roles",palettes}));
