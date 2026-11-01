<script setup lang="ts">
export interface IconProps {
  name: string;
  width?: string;
  height?: string;
}

defineProps<IconProps>();
</script>

<template>
    <svg 
        class="icon" aria-hidden="true" 
        :style="{
            width: width || '100%',
            height: height || '100%'
        }"
    >
        <use :xlink:href="`#${name}`"></use>
    </svg>
</template>

<style lang="scss" scoped>
.icon{
    fill: currentColor;
    overflow: hidden;
}
</style>
