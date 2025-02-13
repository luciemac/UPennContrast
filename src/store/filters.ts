import {
  getModule,
  Action,
  Module,
  Mutation,
  VuexModule
} from "vuex-module-decorators";
import store from "./root";

import main from "./index";
import annotation from "./annotation";
import properties from "./properties";

import Vue from "vue";

import {
  IAnnotation,
  ITagAnnotationFilter,
  IPropertyAnnotationFilter,
  IROIAnnotationFilter,
  IIdAnnotationFilter,
  IGeoJSPoint,
  IShapeAnnotationFilter,
  AnnotationShape
} from "./model";

import geo from "geojs";

@Module({ dynamic: true, store, name: "filters" })
export class Filters extends VuexModule {
  // Annotation browser filters
  tagFilter: ITagAnnotationFilter = {
    id: "tagFilter",
    exclusive: false,
    enabled: false,
    tags: []
  };

  shapeFilter: IShapeAnnotationFilter = {
    id: "shapeFilter",
    enabled: false,
    exclusive: true,
    shape: AnnotationShape.Point
  };

  propertyFilters: IPropertyAnnotationFilter[] = [];

  roiFilters: IROIAnnotationFilter[] = [];
  emptyROIFilter: IROIAnnotationFilter | null = null;

  selectionFilter: IIdAnnotationFilter = {
    enabled: false,
    exclusive: true,
    id: "selection",
    annotationIds: []
  };

  filterIds: string[] = [];

  histograms: {
    [propertyId: string]: { count: number; min: number; max: number }[];
  } = {};

  @Mutation
  addFilterId(id: string) {
    if (!this.filterIds.includes(id)) {
      this.filterIds = [...this.filterIds, id];
    }
  }

  @Mutation
  removeFilterId(id: string) {
    if (this.filterIds.includes(id)) {
      this.filterIds = this.filterIds.filter(testId => id !== testId);
    }
  }

  @Mutation
  addSelectionAsFilter() {
    const selection = annotation.selectedAnnotations.map(
      (value: IAnnotation) => value.id
    );
    this.selectionFilter = {
      enabled: true,
      exclusive: true,
      id: "selection",
      annotationIds: selection
    };
  }

  @Mutation
  clearSelection() {
    this.selectionFilter = {
      enabled: false,
      exclusive: true,
      id: "selection",
      annotationIds: []
    };
  }

  @Mutation
  newROIFilter() {
    this.emptyROIFilter = {
      id: `Region Filter ${this.roiFilters.length}`,
      exclusive: true,
      enabled: true,
      roi: []
    };
  }

  @Mutation
  removeROIFilter(id: string) {
    {
      this.roiFilters = this.roiFilters
        .filter((filter: IROIAnnotationFilter) => filter.id !== id)
        .map((filter: IROIAnnotationFilter, index) => ({
          ...filter,
          id: `Region Filter ${index}`
        }));
    }
  }

  @Mutation
  validateNewROIFilter(roi: IGeoJSPoint[]) {
    if (!this.emptyROIFilter) {
      return;
    }
    this.roiFilters = [...this.roiFilters, { ...this.emptyROIFilter, roi }];
    this.emptyROIFilter = null;
  }

  @Mutation
  cancelROISelection() {
    this.emptyROIFilter = null;
  }

  @Mutation
  toggleRoiFilterEnabled(id: string) {
    const filter = this.roiFilters.find(
      (filter: IROIAnnotationFilter) => filter.id === id
    );
    if (filter) {
      this.roiFilters = [
        ...this.roiFilters.filter(
          (value: IROIAnnotationFilter) => value.id !== id
        ),
        { ...filter, enabled: !filter.enabled }
      ];
    }
  }

  get filteredAnnotations() {
    return annotation.annotations.filter((annotation: IAnnotation) => {
      // shape filter
      if (
        this.shapeFilter.enabled &&
        annotation.shape !== this.shapeFilter.shape
      ) {
        return false;
      }

      // Selection filter
      if (
        this.selectionFilter.enabled &&
        !this.selectionFilter.annotationIds.includes(annotation.id)
      ) {
        return false;
      }

      // Tag filter
      if (this.tagFilter.enabled) {
        const hasAllTags = this.tagFilter.tags.reduce(
          (val: boolean, tag: string) => val && annotation.tags.includes(tag),
          true
        );
        if (
          hasAllTags &&
          this.tagFilter.exclusive &&
          !annotation.tags
            .map((tag: string) => this.tagFilter.tags.includes(tag))
            .every((val: boolean) => val)
        ) {
          return false;
        }

        if (!hasAllTags) {
          return false;
        }
      }

      // Property filters
      const propertyValues = properties.propertyValues[annotation.id] || {};
      const matchesProperties = this.propertyFilters
        .filter((filter: IPropertyAnnotationFilter) => filter.enabled)
        .reduce((val: boolean, filter: IPropertyAnnotationFilter) => {
          if (!val) {
            return false;
          }
          if (!Object.keys(propertyValues).includes(filter.propertyId)) {
            return false;
          }
          const value = propertyValues[filter.propertyId];
          return value >= filter.range.min && value <= filter.range.max;
        }, true);

      if (!matchesProperties) {
        return false;
      }

      // ROI filters
      const roiFilters = this.roiFilters.filter(
        (filter: IROIAnnotationFilter) => filter.enabled
      );
      if (!roiFilters.length) {
        return true;
      }
      const isInROI = roiFilters.reduce(
        (isIn, filter: IROIAnnotationFilter) => {
          return (
            isIn ||
            annotation.coordinates.reduce(
              (onePointIn: boolean, point: IGeoJSPoint) =>
                onePointIn || geo.util.pointInPolygon(point, filter.roi),
              false
            )
          );
        },
        false
      );

      return isInROI;
    });
  }

  @Mutation
  public updatePropertyFilter(value: IPropertyAnnotationFilter) {
    this.propertyFilters = [
      ...this.propertyFilters.filter(
        (filter: IPropertyAnnotationFilter) =>
          filter.propertyId !== value.propertyId
      ),
      value
    ];
  }

  @Mutation
  public setShapeFilter(filter: IShapeAnnotationFilter) {
    this.shapeFilter = filter;
  }

  @Mutation
  public setTagFilter(filter: ITagAnnotationFilter) {
    this.tagFilter = filter;
  }

  @Mutation
  public addTagToTagFilter(tag: string) {
    if (this.tagFilter.tags.includes(tag)) {
      return;
    }
    this.tagFilter = Object.assign({}, this.tagFilter, {
      tags: [...this.tagFilter.tags, tag]
    });
  }

  @Mutation
  public setPropertyHistogram({
    propertyId,
    histogram
  }: {
    propertyId: string;
    histogram: { count: number; min: number; max: number }[];
  }) {
    Vue.set(this.histograms, propertyId, histogram);
  }

  @Action
  async updateHistograms() {
    this.filterIds.forEach((id: string) => {
      if (!main.dataset) {
        return;
      }
      properties.propertiesAPI
        .getPropertyHistogram(main.dataset.id, id)
        .then((histogram: { count: number; min: number; max: number }[]) => {
          this.setPropertyHistogram({ propertyId: id, histogram });
        });
    });
  }
}

export default getModule(Filters);
