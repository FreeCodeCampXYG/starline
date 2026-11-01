<script setup lang="ts">
export interface IconProps {
    text: string;
    subtext?: string | number;
}

defineProps<IconProps>();
</script>

<template>
    <div class="flex flex-row items-baseline">
        <span class="block text-first font-semibold">{{ text }}</span>
        <template v-if="subtext && ['string', 'number'].includes(typeof subtext)">
            <div
                style="margin: 0 10px; width: 1px; height: 10px; background: var(--separator-color);transform: scaleX(.75);">
            </div>
            <span class="block text-four">
                {{ subtext }}
            </span>
        </template>
    </div>
</template>

<style lang="scss" scoped></style>
