<template>
  <v-select
    v-model="content"
    :items="templates"
    item-text="name"
    item-value="type"
    label="Select a tool type to add"
    return-object
    dense
  >
  </v-select>
</template>
<script lang="ts">
import { Vue, Component, Watch, Prop } from "vue-property-decorator";
import toolsStore from "@/store/tool";
import ToolConfiguration from "@/tools/creation/ToolConfiguration.vue";

@Component({
  components: {
    ToolConfiguration
  }
})
export default class ToolTypeSelection extends Vue {
  readonly store = toolsStore;

  @Prop()
  private value: any;

  content: any = null;

  @Watch("content")
  handleChange() {
    this.$emit("input", this.content);
  }

  mounted() {
    if (this.value) {
      this.content = this.value;
    } else {
      this.initialize();
    }
  }

  get templates() {
    return this.store.toolTemplateList;
  }

  @Watch("templates")
  @Watch("value")
  initialize() {
    // Set initial value
    if (!this.value && this.templates.length) {
      this.content = null;
      this.handleChange();
    }
  }
}
</script>
