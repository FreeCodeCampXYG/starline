<script setup lang="ts">
import { pxToRem } from "../../../utils";
import { ref, watch, nextTick, computed, onMounted } from "vue";
// import { useResizeObserver } from "@vueuse/core";

export type HiMultiTextParams = {
  text: string;
  unit?: string;
  color?: string;
  unitColor?: string;
  unitSize?: number;
};

export type HiTextMultiProps = {
  size: number | [number, number];
  list: HiMultiTextParams[];
};

const props = withDefaults(defineProps<HiTextMultiProps>(), {});

const $text = ref<HTMLElement>();
const is12PxLimited = ref(0);
const initFontSize = props.size instanceof Array ? props.size[0] : props.size;
const amendedText = ref<string[]>([]);
const needOmit = ref<boolean[]>([]);
const textFontSize = ref(initFontSize);

const computedText = computed(() =>
  amendedText.value.map((value, index) => {
    if (needOmit.value[index]) {
      return `${value}...`;
    }
    return value;
  })
);

const resizeFontSize = ($: HTMLElement, fs: number | null = null) => {
  const height = $.getBoundingClientRect().height;
  const lineHeight = parseFloat(getComputedStyle($).lineHeight);
  let fontSize = fs || initFontSize;
  let needRecur = false;
  let overflow = false;

  // console.log(height, lineHeight, $.getBoundingClientRect().height);
  // console.dir($);

  // 1. 先查看是否溢出行高
  // ceil 为了防止 lineHeight 误差
  if (Math.floor(height) > Math.ceil(lineHeight)) {
    // 2. 如果 size 设置的[不是数组]或者[当前字体大小已经小于等于最小字体大小]，则设置省略号
    // 否则进行字体缩放
    if (typeof props.size === "number" || fontSize <= props.size[1]) {
      // 3. 如果已经是最小字号了，根据设置的行数考虑要不要换行
      if (Math.floor(height) > Math.ceil(lineHeight)) {
        overflow = true;
      }
    } else {
      needRecur = true;
      // PC端浏览器可能限制了最小字体为 12px
      // 为了防止死循环记录次数，累计超过2次则不进行递归
      if (fontSize === 12) {
        is12PxLimited.value += 1;
        if (is12PxLimited.value >= 2) {
          needRecur = false;
          overflow = true;
        }
      }

      fontSize -= 1;
    }
  }

  textFontSize.value = fontSize;
  if (needRecur) {
    nextTick(() => {
      resizeFontSize($, fontSize);
    });
  } else if (overflow) {
    let stop = false;
    let index = amendedText.value.length - 1;

    while (index >= 0) {
      needOmit.value[index] = true;
      if (amendedText.value[index].length === 1) {
        if (index === 0) {
          // 每个主文本都缩放到只剩一个字符则设置停止递归标记
          stop = true;
        }
        index -= 1;
      } else {
        amendedText.value[index] = amendedText.value[index].slice(0, -1);
        index = -1;
      }
    }
    if (stop) {
      return;
    }
    nextTick(() => {
      resizeFontSize($, fontSize);
    });
  }
};

const run = () => {
  // 1. 赋值为初值
  amendedText.value = props.list.map((item) => item.text);
  needOmit.value = props.list.map(() => false);
  textFontSize.value = initFontSize;
  // 2. 调整大小
  nextTick(() => {
    resizeFontSize($text.value!, initFontSize);
  });
};

onMounted(() => {
  watch(
    () => props.list,
    () => {
      run();
    },
    {
      immediate: true,
    }
  );

  // useResizeObserver($text, () => run());
});
</script>

<template>
  <span
    ref="$text"
    class="hi-multi-text"
    :style="{
      fontSize: pxToRem(textFontSize),
    }"
  >
    <template v-for="(item, index) in list" :key="index">
      <span
        :style="{
          color: item.color || 'var(--text-color--first)',
        }"
      >
        {{ computedText[index] }}</span
      ><span
        v-if="item.unit"
        class="ml-[.2rem]"
        :style="{
          fontSize: pxToRem(item.unitSize || 12),
          color: item.unitColor || 'var(--text-color--second)',
          marginRight: pxToRem(index === list.length - 1 ? 0 : 2),
        }"
      >
        {{ item.unit! }}
      </span>
    </template>
  </span>
</template>

<style lang="scss" scoped>
.hi-multi-text {
  @apply inline-block break-words whitespace-pre-line max-w-full;
  span {
    transition: color 0.2s ease;
  }
}
</style>
