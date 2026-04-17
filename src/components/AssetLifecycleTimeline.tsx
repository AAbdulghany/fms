import { Asset, AssetLifecycleEvent } from "../lib/types";

interface AssetLifecycleTimelineProps {
  asset: Asset;
  events?: AssetLifecycleEvent[];
}

export function AssetLifecycleTimeline({ asset, events: _events = [] }: AssetLifecycleTimelineProps) {
  const currentAge = asset.age_years;
  const expectedLifespan = asset.expected_lifespan_years;
  const percentComplete = Math.min((currentAge / expectedLifespan) * 100, 100);

  return (
    <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-6">
      <h3 className="mb-4 text-lg font-medium text-neutral-900">Asset Lifecycle Timeline</h3>
      
      {/* Desktop: Horizontal Timeline */}
      <div className="hidden sm:block">
        <div className="relative pt-8">
          {/* Timeline bar */}
          <div className="absolute left-0 top-12 h-1 w-full bg-neutral-200" />
          
          {/* Active portion */}
          <div
            className={`absolute left-0 top-12 h-1 ${
              asset.lifecycle_status === "end_of_life"
                ? "bg-error-main"
                : asset.lifecycle_status === "warning"
                ? "bg-warning-main"
                : "bg-success-main"
            }`}
            style={{ width: `${Math.min(percentComplete, 100)}%` }}
          />
          
          {/* Events */}
          <div className="relative flex justify-between">
            {/* Installation */}
            <div className="flex flex-col items-center" style={{ marginLeft: "0%" }}>
              <div className="z-10 h-4 w-4 rounded-full bg-primary-500 ring-4 ring-neutral-0" />
              <div className="mt-2 text-center">
                <p className="text-xs font-medium text-neutral-700">Installed</p>
                <p className="text-xs text-neutral-500">
                  {new Date(asset.installation_date).toLocaleDateString()}
                </p>
              </div>
            </div>
            
            {/* Current position */}
            {percentComplete < 100 && (
              <div
                className="absolute flex flex-col items-center"
                style={{ left: `${percentComplete}%`, transform: "translateX(-50%)" }}
              >
                <div className="z-10 h-4 w-4 animate-pulse rounded-full bg-primary-600 ring-4 ring-neutral-0" />
                <div className="mt-2 text-center">
                  <p className="text-xs font-medium text-primary-600">NOW</p>
                  <p className="text-xs text-neutral-500">{currentAge.toFixed(1)} years</p>
                </div>
              </div>
            )}
            
            {/* Expected EOL */}
            <div className="flex flex-col items-center" style={{ marginRight: "0%" }}>
              <div
                className={`z-10 h-4 w-4 rounded-full ring-4 ring-neutral-0 ${
                  percentComplete >= 100 ? "bg-error-main" : "bg-neutral-400"
                }`}
              />
              <div className="mt-2 text-center">
                <p className="text-xs font-medium text-neutral-700">Expected EOL</p>
                <p className="text-xs text-neutral-500">{expectedLifespan} years</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Status indicator */}
        <div className="mt-6 text-center text-sm">
          {asset.lifecycle_status === "warning" && (
            <p className="text-warning-dark">
              ⚠️ Warning: Asset is {asset.lifespan_percentage}% through expected lifespan
            </p>
          )}
          {asset.lifecycle_status === "end_of_life" && (
            <p className="text-error-main">
              🔴 End of Life: Asset has exceeded expected lifespan
            </p>
          )}
          {asset.lifecycle_status === "active" && (
            <p className="text-success-main">
              ✓ Active: Asset operating normally ({asset.lifespan_percentage}% of lifespan used)
            </p>
          )}
        </div>
      </div>
      
      {/* Mobile: Vertical Timeline */}
      <div className="sm:hidden">
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <div className="h-4 w-4 rounded-full bg-primary-500" />
              <div className="h-full w-0.5 bg-neutral-200" />
            </div>
            <div className="flex-1 pb-4">
              <p className="text-sm font-medium text-neutral-900">Installed</p>
              <p className="text-xs text-neutral-500">
                {new Date(asset.installation_date).toLocaleDateString()}
              </p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <div className="h-4 w-4 animate-pulse rounded-full bg-primary-600" />
              <div className="h-full w-0.5 bg-neutral-200" />
            </div>
            <div className="flex-1 pb-4">
              <p className="text-sm font-medium text-primary-600">NOW</p>
              <p className="text-xs text-neutral-500">
                {currentAge.toFixed(1)} years old • {asset.lifespan_percentage}% of lifespan used
              </p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <div
                className={`h-4 w-4 rounded-full ${
                  percentComplete >= 100 ? "bg-error-main" : "bg-neutral-400"
                }`}
              />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-neutral-900">Expected EOL</p>
              <p className="text-xs text-neutral-500">{expectedLifespan} years</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
