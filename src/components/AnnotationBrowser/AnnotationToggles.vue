<template>
  <v-expansion-panel>
    <v-expansion-panel-header>
      Annotation Controls
    </v-expansion-panel-header>
    <v-expansion-panel-content>
      <v-list dense class="py-0">
        <v-list-item>
          <v-checkbox
            hide-details
            v-model="drawAnnotations"
            dense
            label="Show Annotations"
          ></v-checkbox>
        </v-list-item>
      </v-list>
      <v-list dense value="true" class="py-0">
        <v-list-item>
          <v-checkbox
            hide-details
            :disabled="!drawAnnotations"
            dense
            v-model="filteredDraw"
            label="Show Only Annotations Passing Filter"
          ></v-checkbox>
        </v-list-item>
        <v-list-item>
          <v-checkbox
            hide-details
            :disabled="!drawAnnotations"
            dense
            v-model="drawConnections"
            label="Show Connections"
          ></v-checkbox>
        </v-list-item>
      </v-list>
    </v-expansion-panel-content>
  </v-expansion-panel>
</template>

<script lang="ts">
import { Vue, Component } from "vue-property-decorator";
import store from "@/store";

@Component({
  components: {}
})
export default class AnnotationToggles extends Vue {
  readonly store = store;

  get drawAnnotations() {
    return this.store.drawAnnotations;
  }

  set drawAnnotations(value: boolean) {
    this.store.setDrawAnnotations(value);
  }

  get filteredDraw() {
    return this.store.filteredDraw;
  }

  set filteredDraw(value: boolean) {
    this.store.setFilteredDraw(value);
  }

  get drawActive() {
    return this.store.drawActive;
  }

  set drawActive(value: boolean) {
    this.store.setDrawActive(value);
  }

  get drawConnections() {
    return this.store.drawAnnotationConnections;
  }

  set drawConnections(value: boolean) {
    this.store.setDrawAnnotationConnections(value);
  }
}
</script>
