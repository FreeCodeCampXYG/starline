<script setup lang="ts">
import { ref, toRefs, computed, onMounted, reactive, shallowRef, watch, watchEffect } from "vue";

import type { SliderProps } from "../slider/index.vue";
import Slider from "../slider/index.vue";
import XJTitle from "../xj-title/index.vue";
import type { CoarseSliderProps } from "../slider/CoarseSlider.vue";
import CoarseSlider from "../slider/CoarseSlider.vue";

export type HiSliderMarks = Array<{
  value: number;
  text: string;
}>;

export type HiSliderBreakpoints = number[];

export type SliderCardProps = CoarseSliderProps & SliderProps & {
  text?: string;
  subtext?: string | null;
  subtextFunc?: (v?: string | number) => string;
  disabled?: boolean;
  isCard?: boolean;
  type?: string;
  sliderType?: string;
};

const emits = defineEmits(["change", "complete"]);

const props = withDefaults(defineProps<SliderCardProps>(), {
  isCard: true,
  scale: "auto",
  blockStyle: () => ({}),
  trackStyle: () => ({}),
});
const sliderValues = ref<string|number>();

const onChange = (value) => {
  emits("change", value);
}
const onComplete = (value) => {
  emits("complete", value);
}
watch(
  () => props.value,
  value => {
    sliderValues.value = value;
  },
  {
    immediate: true,
  }
);
</script>

<template>
  <div
    :class="{ 'card': isCard, 'sliderCard': isCard, 'cardDisabled': disabled }"
  >
    <XJTitle 
      v-if="text"
      :text="text" 
      :subtext="subtext ? subtext : subtextFunc ? subtextFunc(sliderValues ?? value) : `${sliderValues ?? value}${unit || ''}`" 
    />
    <CoarseSlider
      :style="{ 'margin-top': text ? '.5rem' : 0 }"
      :value="value"
      :range="range"
      :unit="unit"
      :scale="scale"
      :block-style="blockStyle"
      :track-color="trackColor"
      :track-tint-color="trackTintColor"
      :show-button="showButton"
      :show-mark="showMark"
      :icons="icons"
      :container-height="containerHeight"
      :icon-size="iconSize"
      @change="
        (value: number) => {
          console.log('change--->', value)
          sliderValues = Math.round(value);
          onChange?.(Math.round(value));
        }
      "
      @complete="onComplete"
      v-if="sliderType === 'COARSE'"
    />
    <Slider
      :style="{ 'margin-top': text ? '.5rem' : 0 }"
      :value="value"
      :range="range"
      :unit="unit"
      :scale="scale"
      :block-style="blockStyle"
      :track-color="trackColor"
      :track-tint-color="trackTintColor"
      :show-button="showButton"
      :show-mark="showMark"
      @change="
        (value: number) => {
          sliderValues = Math.round(value);
          onChange?.(Math.round(value));
        }
      "
      @complete="onComplete"
      v-else
    />
  </div>
</template>

<style lang="scss">
  .sliderCard {
    @apply pb-[1.7rem];
  }
</style>
