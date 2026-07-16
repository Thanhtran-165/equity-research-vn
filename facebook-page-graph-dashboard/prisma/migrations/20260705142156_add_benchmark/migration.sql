-- CreateTable
CREATE TABLE "CompetitorPage" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "pageName" TEXT NOT NULL,
    "pageUrl" TEXT NOT NULL,
    "category" TEXT NOT NULL DEFAULT 'khac',
    "description" TEXT,
    "followersLatest" INTEGER,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "notes" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "CompetitorMetricSnapshot" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "competitorPageId" INTEGER NOT NULL,
    "periodStart" TEXT NOT NULL,
    "periodEnd" TEXT NOT NULL,
    "followers" INTEGER NOT NULL DEFAULT 0,
    "postsCount" INTEGER NOT NULL DEFAULT 0,
    "reactionsCount" INTEGER NOT NULL DEFAULT 0,
    "commentsCount" INTEGER NOT NULL DEFAULT 0,
    "sharesCount" INTEGER NOT NULL DEFAULT 0,
    "videoViews" INTEGER,
    "topPostUrl" TEXT,
    "topPostEngagement" INTEGER,
    "activeAds" BOOLEAN,
    "dominantTopic" TEXT,
    "publicEngagement" INTEGER,
    "publicEngagementPerPost" REAL,
    "engagementPer1kFollowers" REAL,
    "avgReactionsPerPost" REAL,
    "avgCommentsPerPost" REAL,
    "avgSharesPerPost" REAL,
    "videoViewsPerFollower" REAL,
    "commentIntensity" REAL,
    "shareIntensity" REAL,
    "postingFrequencyPerDay" REAL,
    "benchmarkScore" REAL,
    "rawJson" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "CompetitorMetricSnapshot_competitorPageId_fkey" FOREIGN KEY ("competitorPageId") REFERENCES "CompetitorPage" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "OwnPagePublicComparableSnapshot" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "pageId" TEXT NOT NULL,
    "periodStart" TEXT NOT NULL,
    "periodEnd" TEXT NOT NULL,
    "followers" INTEGER NOT NULL DEFAULT 0,
    "postsCount" INTEGER NOT NULL DEFAULT 0,
    "reactionsCount" INTEGER NOT NULL DEFAULT 0,
    "commentsCount" INTEGER NOT NULL DEFAULT 0,
    "sharesCount" INTEGER NOT NULL DEFAULT 0,
    "videoViews" INTEGER,
    "publicEngagement" INTEGER,
    "publicEngagementPerPost" REAL,
    "engagementPer1kFollowers" REAL,
    "avgReactionsPerPost" REAL,
    "avgCommentsPerPost" REAL,
    "avgSharesPerPost" REAL,
    "videoViewsPerFollower" REAL,
    "commentIntensity" REAL,
    "shareIntensity" REAL,
    "postingFrequencyPerDay" REAL,
    "benchmarkScore" REAL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "CompetitorPage_pageUrl_key" ON "CompetitorPage"("pageUrl");

-- CreateIndex
CREATE INDEX "CompetitorPage_category_idx" ON "CompetitorPage"("category");

-- CreateIndex
CREATE INDEX "CompetitorPage_isActive_idx" ON "CompetitorPage"("isActive");

-- CreateIndex
CREATE INDEX "CompetitorMetricSnapshot_periodStart_periodEnd_idx" ON "CompetitorMetricSnapshot"("periodStart", "periodEnd");

-- CreateIndex
CREATE UNIQUE INDEX "CompetitorMetricSnapshot_competitorPageId_periodStart_periodEnd_key" ON "CompetitorMetricSnapshot"("competitorPageId", "periodStart", "periodEnd");

-- CreateIndex
CREATE INDEX "OwnPagePublicComparableSnapshot_periodStart_periodEnd_idx" ON "OwnPagePublicComparableSnapshot"("periodStart", "periodEnd");

-- CreateIndex
CREATE UNIQUE INDEX "OwnPagePublicComparableSnapshot_pageId_periodStart_periodEnd_key" ON "OwnPagePublicComparableSnapshot"("pageId", "periodStart", "periodEnd");
