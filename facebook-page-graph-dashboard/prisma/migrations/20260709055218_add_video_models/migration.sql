-- CreateTable
CREATE TABLE "VideoAsset" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "externalVideoId" TEXT NOT NULL,
    "sharedVideoId" TEXT,
    "pageId" TEXT,
    "title" TEXT,
    "createdTime" TEXT,
    "permalinkUrl" TEXT,
    "matchedPostId" TEXT,
    "durationSeconds" INTEGER,
    "source" TEXT NOT NULL DEFAULT 'meta_business_suite_csv',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "VideoDailyMetric" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "videoAssetId" INTEGER NOT NULL,
    "date" TEXT NOT NULL,
    "reach" INTEGER,
    "videoViews3s" INTEGER,
    "watchTimeSeconds" REAL,
    "avgWatchTime" REAL,
    "reactions" INTEGER,
    "comments" INTEGER,
    "shares" INTEGER,
    "source" TEXT NOT NULL DEFAULT 'meta_business_suite_csv',
    "importBatchId" INTEGER,
    "rawRowJson" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "VideoDailyMetric_videoAssetId_fkey" FOREIGN KEY ("videoAssetId") REFERENCES "VideoAsset" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "VideoLifetimeMetric" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "videoAssetId" INTEGER NOT NULL,
    "reach" INTEGER,
    "videoViews3s" INTEGER,
    "videoViews1min" INTEGER,
    "uniqueViewers3s" INTEGER,
    "uniqueViewers1min" INTEGER,
    "watchTimeSeconds" REAL,
    "avgWatchTime" REAL,
    "reactions" INTEGER,
    "comments" INTEGER,
    "shares" INTEGER,
    "source" TEXT NOT NULL DEFAULT 'meta_business_suite_csv',
    "importBatchId" INTEGER,
    "rawRowJson" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "VideoLifetimeMetric_videoAssetId_fkey" FOREIGN KEY ("videoAssetId") REFERENCES "VideoAsset" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "VideoAsset_externalVideoId_key" ON "VideoAsset"("externalVideoId");

-- CreateIndex
CREATE INDEX "VideoAsset_pageId_idx" ON "VideoAsset"("pageId");

-- CreateIndex
CREATE INDEX "VideoAsset_matchedPostId_idx" ON "VideoAsset"("matchedPostId");

-- CreateIndex
CREATE INDEX "VideoDailyMetric_date_idx" ON "VideoDailyMetric"("date");

-- CreateIndex
CREATE INDEX "VideoDailyMetric_videoAssetId_date_idx" ON "VideoDailyMetric"("videoAssetId", "date");

-- CreateIndex
CREATE UNIQUE INDEX "VideoDailyMetric_videoAssetId_date_key" ON "VideoDailyMetric"("videoAssetId", "date");

-- CreateIndex
CREATE UNIQUE INDEX "VideoLifetimeMetric_videoAssetId_key" ON "VideoLifetimeMetric"("videoAssetId");

-- CreateIndex
CREATE INDEX "VideoLifetimeMetric_videoAssetId_idx" ON "VideoLifetimeMetric"("videoAssetId");
