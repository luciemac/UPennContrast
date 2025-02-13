<template>
  <div>
    <v-card class="pa-1">
      <v-card-title>
        Add a new tool
      </v-card-title>
      <v-card-text class="pa-1">
        <v-card>
          <v-card-text class="pa-1">
            <v-container>
              <v-row>
                <v-col>
                  <v-text-field label="Tool Name" v-model="toolName" dense>
                  </v-text-field>
                </v-col>
                <v-col>
                  <!-- Pick which template should be used for the tool configuration -->
                  <tool-type-selection v-model="selectedItemTemplate">
                  </tool-type-selection>
                </v-col>
              </v-row>
              <v-row>
                <v-col>
                  <v-textarea
                    label="Tool Description"
                    v-model="toolDescription"
                    auto-grow
                    rows="2"
                    dense
                  >
                  </v-textarea>
                </v-col>
              </v-row>
            </v-container>
          </v-card-text>
        </v-card>
        <!-- Form elements generated from the template -->
        <tool-configuration
          :template="selectedItemTemplate"
          v-model="toolValues"
          @submit="createTool"
          @reset="reset"
          ref="toolConfiguration"
        />
      </v-card-text>
      <v-card-actions>
        <div class="button-bar">
          <v-spacer></v-spacer>
          <v-btn class="mr-4" color="primary" @click="createTool">
            ADD TOOL TO THE CURRENT TOOLSET
          </v-btn>
          <v-btn class="mr-4" color="warning" @click="close">CANCEL</v-btn>
        </div>
      </v-card-actions>
    </v-card>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Watch, Prop } from "vue-property-decorator";
import store from "@/store";
import toolsStore from "@/store/tool";
import propertiesStore from "@/store/properties";

import ToolConfiguration from "@/tools/creation/ToolConfiguration.vue";
import ToolTypeSelection from "@/tools/creation/ToolTypeSelection.vue";
import { logError } from "@/utils/log";

const defaultValues = {
  name: "New Tool",
  description: ""
};

// Popup for new tool configuration
@Component({
  components: {
    ToolConfiguration,
    ToolTypeSelection
  }
})
export default class ToolCreation extends Vue {
  readonly store = store;
  readonly toolsStore = toolsStore;
  readonly propertyStore = propertiesStore;

  toolValues: any = { ...defaultValues };

  selectedItemTemplate: any = null;
  errorMessages: string[] = [];
  successMessages: string[] = [];

  toolName = "New Tool";
  toolDescription = "";

  @Prop()
  readonly open: any;

  createTool() {
    if (this.selectedItemTemplate) {
      const tool = {
        type: this.selectedItemTemplate.type,
        template: this.selectedItemTemplate,
        values: this.toolValues
      };
      const name = this.toolName || "Unnamed Tool";
      const description = this.toolDescription || "";
      // Create an empty tool to get the id
      this.toolsStore.createTool({ name, description }).then(tool => {
        if (tool === null) {
          logError("Failed to create a new tool on the server");
          return;
        }
        tool.template = this.selectedItemTemplate;
        tool.values = this.toolValues;
        tool.type = this.selectedItemTemplate.type;
        if (tool.type === "segmentation") {
          const { image } = tool.values.image;
          this.propertyStore.requestWorkerInterface(image);
        }

        // Update this tool with actual values
        this.toolsStore.updateTool(tool).then(() => {
          this.store.syncConfiguration();
        });

        // Add this tool to the current toolset
        this.toolsStore.addToolIdsToCurrentToolset({ ids: [tool.id] });

        // Save
        this.store.syncConfiguration();

        this.close();
      });
    }
  }

  @Watch("open")
  reset() {
    this.toolName = "New Tool";
    this.toolDescription = "";

    if (!this.$refs.toolConfiguration) {
      return;
    }

    const toolConfiguration = this.$refs.toolConfiguration as ToolConfiguration;
    if (toolConfiguration) {
      toolConfiguration.reset();
    }
  }

  close() {
    this.reset();
    this.$emit("done");
  }
}
</script>
