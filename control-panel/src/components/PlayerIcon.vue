<script setup lang="ts">
defineProps<{ name: string }>();
const paths: Record<string, string> = {
  play: "M9 5l11 7-11 7z", pause: "M8 5v14M16 5v14", next: "M5 5l10 7-10 7zM19 5v14",
  previous: "M19 5L9 12l10 7zM5 5v14", stop: "M6 6h12v12H6z",
  queue: "M4 6h16M4 12h16M4 18h11", repeat: "M5 8h12l-3-3m3 3-3 3M19 16H7l3 3m-3-3 3-3",
  "repeat-one": "M5 8h12l-3-3m3 3-3 3M19 16H7l3 3m-3-3 3-3M12 10v4",
  shuffle: "M4 6h3l10 12h3m-3-3 3 3-3 3M4 18h3l10-12h3m-3-3 3 3-3 3",
  music: "M9 17V5l11-2v12M9 9l11-2M9 17c0 3-6 4-6 1s6-4 6-1m11-2c0 3-6 4-6 1s6-4 6-1"
};
</script>
<template><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path :d="paths[name] || paths.music" /></svg></template>
