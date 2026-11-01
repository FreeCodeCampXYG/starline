<script setup lang="ts">
import { computed, onBeforeMount, ref } from "vue";
import { XJText } from "../../text";

export type XJInputProps = {
  value?: string | number;
  type?: string; // error normal
  showErrorText?: boolean;
  errorText?: string;
  placeholderText?: string;
  regInputFunc?: (value: string) => void
};

const props = withDefaults(defineProps<XJInputProps>(), {
  type: "",
  showErrorText: false,
  errorText: null,
  placeholderText: "",
  regInputFunc: (value) => {
    return { showErrorText: false, errorText: "", type: "", disabledDialogRightButton: false }
  }
});

onBeforeMount(() => {});

let state = ref({
  showErrorText: props.showErrorText,
  errorText: props.errorText,
  type: props.type,
  value: props.value
})

const emits = defineEmits(["change", "error"]);
const onChange = (e) => {
  const value = e.target.value
  console.log(value)
  state.value.value = value
  if (props.regInputFunc) {
    const { showErrorText, errorText, type, value: val, disabledDialogRightButton } = props.regInputFunc(value)
    state.value.showErrorText = showErrorText
    state.value.errorText = errorText
    state.value.type = type
    state.value.value = val
    emits('error', { showErrorText, disabledDialogRightButton })
    // if (showErrorText) {
    //   return;
    // }
  }
  emits('change', state.value.value)
}
</script>

<template>
  <div class="w-full">
    <div class="hi-input">
      <input
          class="w-full" :value="state.value" :placeholder="placeholderText"
          maxlength="100" @input="e => onChange(e)"
      />
      <div :type="state.type" class="hi-input__border"></div>
    </div>
    <div class="h-[2.2rem]" v-if="state.showErrorText && state.errorText && state.errorText.length">
      <XJText :line="0" :text="state.errorText" :size="10" color="var(--error-color)" />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.hi-input {
  @apply relative h-[4.8rem] my-[.4rem] pb-[1.2rem] flex items-end;
  transition: border-color 0.2s cubic-bezier(0.645, 0.045, 0.355, 1);
  -webkit-transition: border-color 0.2s cubic-bezier(0.645, 0.045, 0.355, 1);
  -moz-transition: border-color 0.2s cubic-bezier(0.645, 0.045, 0.355, 1);
  -o-transition: border-color 0.2s cubic-bezier(0.645, 0.045, 0.355, 1);
  -ms-transition: border-color 0.2s cubic-bezier(0.645, 0.045, 0.355, 1);

  .hi-input__border {
    @apply absolute bottom-0 left-0 w-full;
    border-bottom: 0.25px solid var(--separator-color);
  }
  & > input {
    background: transparent;
    outline: none;
    color: var(--color-text-first);
    &::-webkit-input-placeholder {
      color: var(--color-text-second);
    }
  }
  & > input:focus + .hi-input__border {
    outline: none;
    border-bottom-color: var(--separator-color);
  }
  .hi-input__border[type="error"] {
    border-bottom-color: var(--error-color) !important;
  }
}
</style>
