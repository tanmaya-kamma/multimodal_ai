import React from 'react';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { MapContainer } from '../components/map/MapContainer';
import { CellDetailDrawer } from '../components/drawer/CellDetailDrawer';

export const DashboardPage: React.FC = () => {
  return (
    <DashboardLayout>
      <MapContainer />
      <CellDetailDrawer />
    </DashboardLayout>
  );
};
