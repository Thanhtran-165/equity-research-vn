-- DropIndex
DROP INDEX "VideoDailyMetric_videoAssetId_date_key";

-- AlterTable
ALTER TABLE "Post" ADD COLUMN "externalPostId" TEXT;

-- CreateTable
CREATE TABLE "DataReminderRun" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "type" TEXT NOT NULL DEFAULT 'weekly',
    "periodStart" TEXT NOT NULL,
    "periodEnd" TEXT NOT NULL,
    "dueAt" DATETIME NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    "completedAt" DATETIME,
    "notes" TEXT
);

-- CreateTable
CREATE TABLE "DataReminderItem" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "runId" INTEGER NOT NULL,
    "code" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "priority" TEXT NOT NULL,
    "required" BOOLEAN NOT NULL DEFAULT true,
    "platform" TEXT NOT NULL DEFAULT 'Facebook',
    "pageName" TEXT NOT NULL DEFAULT 'Chim Cút',
    "dateRangeStart" TEXT NOT NULL,
    "dateRangeEnd" TEXT NOT NULL,
    "preset" TEXT NOT NULL,
    "dataView" TEXT NOT NULL,
    "contentLevel" TEXT NOT NULL,
    "filterMode" TEXT NOT NULL,
    "expectedFilename" TEXT NOT NULL,
    "purpose" TEXT,
    "note" TEXT,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "metaCreatedAt" DATETIME,
    "downloadedAt" DATETIME,
    "renamedAt" DATETIME,
    "movedToIncomingAt" DATETIME,
    "dryRunAt" DATETIME,
    "appliedAt" DATETIME,
    "notes" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "DataReminderItem_runId_fkey" FOREIGN KEY ("runId") REFERENCES "DataReminderRun" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "BenchmarkPage" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "canonicalUrl" TEXT NOT NULL,
    "platform" TEXT NOT NULL DEFAULT 'facebook',
    "objectType" TEXT NOT NULL DEFAULT 'facebook_page',
    "category" TEXT,
    "benchmarkRole" TEXT NOT NULL DEFAULT 'watchlist',
    "scaleBand" TEXT,
    "collectionFrequency" TEXT,
    "recommendedPostsPerCollection" INTEGER,
    "isOwnPage" BOOLEAN NOT NULL DEFAULT false,
    "activeStatus" TEXT NOT NULL DEFAULT 'active',
    "verificationConfidence" TEXT,
    "lastVerifiedAt" DATETIME,
    "notes" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "BenchmarkAudienceSnapshot" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "benchmarkPageId" INTEGER NOT NULL,
    "capturedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "audienceCount" INTEGER,
    "audienceCountType" TEXT NOT NULL DEFAULT 'unknown',
    "source" TEXT NOT NULL DEFAULT 'manual_public',
    "verificationConfidence" TEXT,
    "notes" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "BenchmarkAudienceSnapshot_benchmarkPageId_fkey" FOREIGN KEY ("benchmarkPageId") REFERENCES "BenchmarkPage" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "BenchmarkPost" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "benchmarkPageId" INTEGER NOT NULL,
    "postUrl" TEXT NOT NULL,
    "postedAt" DATETIME,
    "textSnippet" TEXT,
    "contentType" TEXT,
    "topicTag" TEXT,
    "reactions" INTEGER,
    "comments" INTEGER,
    "shares" INTEGER,
    "publicVideoViews" INTEGER,
    "reactionsObserved" BOOLEAN NOT NULL DEFAULT false,
    "commentsObserved" BOOLEAN NOT NULL DEFAULT false,
    "sharesObserved" BOOLEAN NOT NULL DEFAULT false,
    "publicVideoViewsObserved" BOOLEAN NOT NULL DEFAULT false,
    "comparableEngagement" INTEGER,
    "observedPublicEngagement" INTEGER,
    "metricCoverageScore" REAL,
    "capturedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "source" TEXT NOT NULL DEFAULT 'manual_public',
    "notes" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "BenchmarkPost_benchmarkPageId_fkey" FOREIGN KEY ("benchmarkPageId") REFERENCES "BenchmarkPage" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "BenchmarkPeriodSnapshot" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "benchmarkPageId" INTEGER NOT NULL,
    "periodType" TEXT NOT NULL DEFAULT 'weekly',
    "periodStart" DATETIME NOT NULL,
    "periodEnd" DATETIME NOT NULL,
    "audienceCount" INTEGER,
    "audienceCountType" TEXT,
    "postsCaptured" INTEGER NOT NULL DEFAULT 0,
    "postsWithReactions" INTEGER NOT NULL DEFAULT 0,
    "postsWithComments" INTEGER NOT NULL DEFAULT 0,
    "postsWithShares" INTEGER NOT NULL DEFAULT 0,
    "postsWithVideoViews" INTEGER NOT NULL DEFAULT 0,
    "totalReactions" INTEGER,
    "totalComments" INTEGER,
    "totalShares" INTEGER,
    "totalPublicVideoViews" INTEGER,
    "totalComparableEngagement" INTEGER,
    "totalObservedPublicEngagement" INTEGER,
    "medianComparableEngagementPerPost" REAL,
    "avgComparableEngagementPerPost" REAL,
    "medianObservedEngagementPerPost" REAL,
    "engagementPerFollower" REAL,
    "viralHitRate" REAL,
    "shareRatio" REAL,
    "commentRatio" REAL,
    "metricCoverageScore" REAL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "BenchmarkPeriodSnapshot_benchmarkPageId_fkey" FOREIGN KEY ("benchmarkPageId") REFERENCES "BenchmarkPage" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "BenchmarkCollectionRun" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "weekStart" DATETIME NOT NULL,
    "weekEnd" DATETIME NOT NULL,
    "dueAt" DATETIME NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "snoozedUntil" DATETIME,
    "notes" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    "completedAt" DATETIME
);

-- CreateTable
CREATE TABLE "BenchmarkCollectionItem" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "runId" INTEGER NOT NULL,
    "benchmarkPageId" INTEGER NOT NULL,
    "targetPosts" INTEGER NOT NULL DEFAULT 4,
    "collectedPosts" INTEGER NOT NULL DEFAULT 0,
    "status" TEXT NOT NULL DEFAULT 'not_started',
    "notes" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "BenchmarkCollectionItem_runId_fkey" FOREIGN KEY ("runId") REFERENCES "BenchmarkCollectionRun" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "BenchmarkCollectionItem_benchmarkPageId_fkey" FOREIGN KEY ("benchmarkPageId") REFERENCES "BenchmarkPage" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE INDEX "DataReminderRun_status_idx" ON "DataReminderRun"("status");

-- CreateIndex
CREATE UNIQUE INDEX "DataReminderRun_type_periodStart_periodEnd_key" ON "DataReminderRun"("type", "periodStart", "periodEnd");

-- CreateIndex
CREATE INDEX "DataReminderItem_runId_idx" ON "DataReminderItem"("runId");

-- CreateIndex
CREATE INDEX "DataReminderItem_code_idx" ON "DataReminderItem"("code");

-- CreateIndex
CREATE UNIQUE INDEX "BenchmarkPage_canonicalUrl_key" ON "BenchmarkPage"("canonicalUrl");

-- CreateIndex
CREATE INDEX "BenchmarkPage_benchmarkRole_idx" ON "BenchmarkPage"("benchmarkRole");

-- CreateIndex
CREATE INDEX "BenchmarkPage_objectType_idx" ON "BenchmarkPage"("objectType");

-- CreateIndex
CREATE INDEX "BenchmarkPage_isOwnPage_idx" ON "BenchmarkPage"("isOwnPage");

-- CreateIndex
CREATE INDEX "BenchmarkAudienceSnapshot_benchmarkPageId_capturedAt_idx" ON "BenchmarkAudienceSnapshot"("benchmarkPageId", "capturedAt");

-- CreateIndex
CREATE INDEX "BenchmarkPost_benchmarkPageId_idx" ON "BenchmarkPost"("benchmarkPageId");

-- CreateIndex
CREATE INDEX "BenchmarkPost_capturedAt_idx" ON "BenchmarkPost"("capturedAt");

-- CreateIndex
CREATE UNIQUE INDEX "BenchmarkPost_benchmarkPageId_postUrl_capturedAt_key" ON "BenchmarkPost"("benchmarkPageId", "postUrl", "capturedAt");

-- CreateIndex
CREATE INDEX "BenchmarkPeriodSnapshot_benchmarkPageId_idx" ON "BenchmarkPeriodSnapshot"("benchmarkPageId");

-- CreateIndex
CREATE INDEX "BenchmarkPeriodSnapshot_periodStart_periodEnd_idx" ON "BenchmarkPeriodSnapshot"("periodStart", "periodEnd");

-- CreateIndex
CREATE UNIQUE INDEX "BenchmarkPeriodSnapshot_benchmarkPageId_periodType_periodStart_periodEnd_key" ON "BenchmarkPeriodSnapshot"("benchmarkPageId", "periodType", "periodStart", "periodEnd");

-- CreateIndex
CREATE INDEX "BenchmarkCollectionRun_status_idx" ON "BenchmarkCollectionRun"("status");

-- CreateIndex
CREATE UNIQUE INDEX "BenchmarkCollectionRun_weekStart_weekEnd_key" ON "BenchmarkCollectionRun"("weekStart", "weekEnd");

-- CreateIndex
CREATE INDEX "BenchmarkCollectionItem_runId_idx" ON "BenchmarkCollectionItem"("runId");

-- CreateIndex
CREATE UNIQUE INDEX "BenchmarkCollectionItem_runId_benchmarkPageId_key" ON "BenchmarkCollectionItem"("runId", "benchmarkPageId");

-- CreateIndex
CREATE UNIQUE INDEX "Post_externalPostId_key" ON "Post"("externalPostId");

-- CreateIndex
CREATE UNIQUE INDEX "VideoDailyMetric_videoAssetId_date_source_key" ON "VideoDailyMetric"("videoAssetId", "date", "source");

