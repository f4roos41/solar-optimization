/**
 * Module 1: AOI Definition Tool
 *
 * Interactive polygon drawing component using Mapbox GL Draw.
 * Allows users to define their Area of Interest on the map.
 */

import React, { useEffect, useRef } from 'react';
import MapboxDraw from '@mapbox/mapbox-gl-draw';
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';
import * as turf from '@turf/turf';
import type { Map } from 'mapbox-gl';

interface AOIDrawControlProps {
  map: Map | null;
  onAreaCreated: (geojson: any, area: number) => void;
  onAreaUpdated: (geojson: any, area: number) => void;
}

const AOIDrawControl: React.FC<AOIDrawControlProps> = ({
  map,
  onAreaCreated,
  onAreaUpdated,
}) => {
  const drawRef = useRef<MapboxDraw | null>(null);

  useEffect(() => {
    if (!map) return;

    // Initialize Mapbox Draw
    const draw = new MapboxDraw({
      displayControlsDefault: false,
      controls: {
        polygon: true,
        trash: true,
      },
      defaultMode: 'draw_polygon',
    });

    map.addControl(draw, 'top-left');
    drawRef.current = draw;

    // Event handlers
    const handleCreate = (e: any) => {
      const feature = e.features[0];
      const area = turf.area(feature);
      const areaKm2 = area / 1_000_000; // Convert m² to km²
      onAreaCreated(feature.geometry, areaKm2);
    };

    const handleUpdate = (e: any) => {
      const feature = e.features[0];
      const area = turf.area(feature);
      const areaKm2 = area / 1_000_000;
      onAreaUpdated(feature.geometry, areaKm2);
    };

    map.on('draw.create', handleCreate);
    map.on('draw.update', handleUpdate);

    return () => {
      map.off('draw.create', handleCreate);
      map.off('draw.update', handleUpdate);
      if (drawRef.current) {
        map.removeControl(drawRef.current);
      }
    };
  }, [map, onAreaCreated, onAreaUpdated]);

  return null;
};

export default AOIDrawControl;
