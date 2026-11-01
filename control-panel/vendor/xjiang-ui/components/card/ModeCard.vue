<script setup lang="ts">
import { ref, computed, useAttrs } from "vue";
import IconButton from "../icon-button/index.vue";
import Icon from "../icon/index.vue";
import XJTitle from "../xj-title/index.vue";

export type ModeItemStaticProps = {
  icon?: string;
  size?: number;
  iconSize?: number;
  iconType?: number;
  rounded?: number;
  text: string;
  value?: string | number;
  active?: boolean;
  vActive?: boolean;
}
export type ModeItemProps = ModeItemStaticProps & {
  needLongClick?: boolean;
  onClick?: (v?: string | number, item?: ModeItemStaticProps) => void;
  onLongClick?: (v?: string | number, item?: ModeItemStaticProps) => void;
};
export type ModeCardProps = {
  text?: string;
  subtext?: string;
  disabled?: boolean;
  value?: string | number;
  list: Array<ModeItemProps>;
  isCard?: boolean;
  lineMaxCount?: number;
  iconType?: number;
  onTitleClick?: () => void;
};

let MouseTimer: NodeJS.Timeout;
let isLongClick: boolean = false;
const emits = defineEmits(["click"]);
const _attrs: any = useAttrs();
const onLongClick: (v?: string | number, item?: ModeItemStaticProps) => void = _attrs?.onLongClick;

const props = withDefaults(defineProps<ModeCardProps>(), {
  isCard: true, lineMaxCount: 5, iconType: 0
});
const { text, subtext } = props;
const _onClick = (v?: string | number, item?: ModeItemStaticProps) => {
  if (props.disabled) return;
  emits("click", v, item);
};
const _onLongClick = (v?: string | number, item?: ModeItemStaticProps) => {
  if (props.disabled || !onLongClick) return;
  // emits("longClick", v);
  onLongClick(v, item);
};

const onDown = () => {
  isLongClick = false;
  MouseTimer && clearTimeout(MouseTimer);
  MouseTimer = setTimeout(() => {
    console.log("长按事件");
    isLongClick = true;
  }, 1400)
}
const onUp = (item, v, itemClick, itemLongClick) => {
  MouseTimer && clearTimeout(MouseTimer);
  if (isLongClick && (onLongClick || itemLongClick)) {
    itemLongClick ? itemLongClick(v, item) : _onLongClick(v, item)
  } else {
    itemClick ? itemClick(v, item) : _onClick(v, item)
  }
}

const subtextCustom = computed<string | number>(() => {
  let _subtext: any = subtext;

  if (props.list && props.list.length) {
    const curItem = props.list.find((item, index) => item.value === props?.value);
    if (curItem) {
      _subtext = curItem?.text || curItem?.value;
    }
  }
  return _subtext;
});

const newList = computed<Array<ModeItemProps>>(() => {
  let _list: any = [];

  if (props.list && props.list.length) {
    _list = props.list.map((item, index) => {
      return {
        ...item,
        vActive: 'active' in item ? item?.active : item.value === props?.value
      }
    });
  }
  return _list;
});
</script>

<template>
  <div :class="{ 'card': isCard, 'cardDisabled': disabled }">
    <div class="flex flex-row items-center justify-between" @click="onTitleClick">
      <XJTitle :text="text" :subtext="subtextCustom" v-if="text && text.length" />

      <Icon v-if="onTitleClick" name="icon-arrowright" width="1.3rem" height="1.3rem" color="var(--icon-color)" />
    </div>
    <div v-if="newList" class="modeList">
      <div v-for="(item, index) in newList" :key="index" @mousedown="onDown()"
        @mouseup="onUp(item, item?.value, item?.onClick, item?.onLongClick)" class=" flex flex-col items-center "
        :style="{ 'min-width': `${100 / lineMaxCount}%` }" onselectstart="return false;">
        <div v-if="item.icon" class="modeIcon">
          <Icon :name="`${item.icon}`" :color="item.vActive && 'var(--active-color)'" width="3rem" height="3rem"
            v-if="iconType" />
          <IconButton :name="`${item.icon}`" :rounded="item.rounded" :active="item.vActive" :size="item?.size"
            :iconSize="item?.iconSize" :type="item?.iconType" v-else />
        </div>
        <span class="mt-[2px] text-second"
          :style="{ opacity: ('active' in item ? item?.active : item.value === props?.value) ? 1 : .6 }">{{ item.text
          }}</span>
      </div>
    </div>
  </div>
</template>

<style lang="scss">
.modeList {
  @apply flex flex-row flex-wrap;

  &>div {
    @apply mt-[15px];
    min-width: 20%;
  }

  span {
    text-align: center;
    word-break: break-all;
  }
}
</style>
