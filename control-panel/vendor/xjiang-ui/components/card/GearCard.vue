<script setup lang="ts">
import { ref, computed } from "vue";
import XJTitle from "../xj-title/index.vue";
import Icon from "../icon/index.vue";

export type GearCardProps = {
  text?: string;
  subtext?: string;
  showSubtext?: boolean;
  disabled?: boolean;
  value?: string | number;
  list: Array<{
    text?: string;
    icon?: string;
    value?: string | number;
  }>;
  isCard?: boolean;
};

const emits = defineEmits(["click"]);

const props = withDefaults(defineProps<GearCardProps>(), { isCard: true, showSubtext: true });
const { text, subtext, list } = props;
const onClick = (v?: string | number) => {
  if (props.disabled) return;
  emits("click", v);
};

const subtextCustom = computed<string | number>(() => {
  if (!props.showSubtext) {
    return "";
  }
  let _subtext: any = subtext;

  if (list && list.length) {
    const curItem = list.find((item, index) => item.value === props?.value);
    if (curItem) {
      _subtext = curItem?.text || curItem?.value;
    }
  }
  return _subtext;
});
</script>

<template>
  <div 
    class="buttonCard"
    :class="{ 'card': isCard, 'cardDisabled': disabled }"
  >
    <XJTitle 
      :text="text" 
      :subtext="subtextCustom" 
      v-if="text && text.length"
    />
    <div 
      v-if="list && list.length"
      class="gearList"
    >
      <div
        v-for="(item, index) in list"
        :key="index"
        @click="() => onClick(item?.value)"
        class="flex-1 flex flex-col items-center justify-center text-third button min-h-[3rem]"
        :class="{ 'button-active': item.value === props?.value }"
      >
        <Icon :name="item?.icon" width="1.7rem" height="1.7rem" v-if="item?.icon" />
        <span>{{ item.text }}</span>
      </div>
    </div>
  </div>
</template>

<style lang="scss">
.gearList {
  @apply flex flex-row flex-wrap mt-[10px] p-[4px];
  border-radius: 50px; background-color: var(--icon-button-bg);

  .button {
    padding: 4px 8px; border-radius: 50px;
    &:last-child {
      @apply mr-[0px];
    }
  }
  .button-active {
    @apply text-white;
    background-color: var(--active-color);
  }
}
</style>
