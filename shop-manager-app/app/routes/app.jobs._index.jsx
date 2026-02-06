import { useState, useCallback, useMemo, useEffect } from "react";
import { useLoaderData, useNavigation, useSearchParams, useRevalidator } from "@remix-run/react";
import {
  Page,
  Layout,
  Card,
  IndexTable,
  Badge,
  Button,
  Filters,
  ChoiceList,
  Pagination,
  EmptyState,
  SkeletonPage,
  SkeletonBodyText,
  ProgressBar,
  Frame,
  BlockStack,
  InlineStack,
} from "@shopify/polaris";
import { TitleBar } from "@shopify/app-bridge-react";
import { authenticate } from "../shopify.server";
import { createApiClient } from "../services/api";
import { JobsService } from "../services/jobs";
import { useAppBridgeNavigation } from "../utils/appBridge";

/**
 * Jobs List Loader
 * Fetches jobs with pagination and filtering
 * Requirements: 11.1, 11.2, 11.3
 */
export const loader = async ({ request }) => {
  try {
    const { sessionToken } = await authenticate.admin(request);
    const api = await createApiClient(request, sessionToken);
    const jobsService = new JobsService(api);

    // Parse query parameters
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get("page") || "1");
    const pageSize = parseInt(url.searchParams.get("pageSize") || "50");
    const status = url.searchParams.get("status") || undefined;
    const jobType = url.searchParams.get("jobType") || undefined;

    // Fetch jobs with filters
    const data = await jobsService.list({
      page,
      page_size: pageSize,
      status,
      job_type: jobType,
    });

    return {
      jobs: data.results,
      count: data.count,
      next: data.next,
      previous: data.previous,
      currentPage: page,
      pageSize,
      filters: {
        status,
        jobType,
      },
    };
  } catch (error) {
    console.error("Jobs loader error:", error);
    throw error;
  }
};

/**
 * Jobs List Component
 * Displays jobs in an IndexTable with filters, status badges, progress bars, and pagination
 * Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9
 */
export default function JobsIndex() {
  const data = useLoaderData();
  const navigation = useNavigation();
  const revalidator = useRevalidator();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useAppBridgeNavigation();

  // State management
  const [statusFilter, setStatusFilter] = useState(data?.filters?.status || "");
  const [jobTypeFilter, setJobTypeFilter] = useState(data?.filters?.jobType || "");

  const isLoading = navigation.state === "loading";

  // Check if there are active jobs
  const hasActiveJobs = useMemo(() => {
    return (data?.jobs || []).some(job => job.status === "running" || job.status === "pending");
  }, [data?.jobs]);

  // Auto-refresh for active jobs every 5 seconds
  // Requirements: 11.8
  useEffect(() => {
    if (!hasActiveJobs) return;

    const interval = setInterval(() => {
      revalidator.revalidate();
    }, 5000);

    return () => clearInterval(interval);
  }, [hasActiveJobs, revalidator]);

  // Handle filter changes
  const handleFilterChange = useCallback(
    (filterName, value) => {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("page", "1"); // Reset to first page on filter change

      if (value) {
        newParams.set(filterName, value);
      } else {
        newParams.delete(filterName);
      }

      setSearchParams(newParams);
    },
    [searchParams, setSearchParams]
  );

  // Handle pagination
  const handlePreviousPage = useCallback(() => {
    const newParams = new URLSearchParams(searchParams);
    const currentPage = parseInt(newParams.get("page") || "1");
    if (currentPage > 1) {
      newParams.set("page", String(currentPage - 1));
      setSearchParams(newParams);
    }
  }, [searchParams, setSearchParams]);

  const handleNextPage = useCallback(() => {
    const newParams = new URLSearchParams(searchParams);
    const currentPage = parseInt(newParams.get("page") || "1");
    newParams.set("page", String(currentPage + 1));
    setSearchParams(newParams);
  }, [searchParams, setSearchParams]);

  // Handle job detail navigation with App Bridge
  const handleJobClick = useCallback((jobId) => {
    navigate(`/app/jobs/${jobId}`);
  }, [navigate]);

  // Calculate job duration
  const calculateDuration = (startedAt, completedAt) => {
    if (!startedAt) return "-";
    
    const start = new Date(startedAt);
    const end = completedAt ? new Date(completedAt) : new Date();
    const durationMs = end - start;
    const durationSeconds = Math.floor(durationMs / 1000);
    
    if (durationSeconds < 60) {
      return `${durationSeconds}s`;
    } else if (durationSeconds < 3600) {
      const minutes = Math.floor(durationSeconds / 60);
      return `${minutes}m`;
    } else {
      const hours = Math.floor(durationSeconds / 3600);
      return `${hours}h`;
    }
  };

  // Get status badge tone
  const getStatusTone = (status) => {
    switch (status) {
      case "completed":
        return "success";
      case "failed":
        return "critical";
      case "running":
      case "pending":
        return "warning";
      default:
        return "default";
    }
  };

  // Resource name for IndexTable
  const resourceName = {
    singular: "job",
    plural: "jobs",
  };

  // Build row markup
  const rowMarkup = useMemo(() => {
    return (data?.jobs || []).map((job, index) => (
      <IndexTable.Row
        id={job.id.toString()}
        key={job.id}
        position={index}
        onClick={() => handleJobClick(job.id)}
      >
        <IndexTable.Cell>
          <Button variant="plain" onClick={() => handleJobClick(job.id)}>
            {job.job_type}
          </Button>
        </IndexTable.Cell>
        <IndexTable.Cell>
          <Badge tone={getStatusTone(job.status)}>
            {job.status}
          </Badge>
        </IndexTable.Cell>
        <IndexTable.Cell>
          <BlockStack gap="100">
            <ProgressBar progress={job.progress} />
            <span>{job.progress}%</span>
          </BlockStack>
        </IndexTable.Cell>
        <IndexTable.Cell>
          {job.started_at ? new Date(job.started_at).toLocaleString() : "-"}
        </IndexTable.Cell>
        <IndexTable.Cell>
          {calculateDuration(job.started_at, job.completed_at)}
        </IndexTable.Cell>
      </IndexTable.Row>
    ));
  }, [data?.jobs, handleJobClick]);

  // Show loading skeleton
  if (isLoading) {
    return (
      <SkeletonPage primaryAction>
        <Layout>
          <Layout.Section>
            <Card>
              <BlockStack gap="300">
                <SkeletonBodyText lines={2} />
              </BlockStack>
            </Card>
          </Layout.Section>
          <Layout.Section>
            <Card>
              <BlockStack gap="300">
                <SkeletonBodyText lines={10} />
              </BlockStack>
            </Card>
          </Layout.Section>
        </Layout>
      </SkeletonPage>
    );
  }

  // Show empty state
  if (!data?.jobs || data.jobs.length === 0) {
    return (
      <Page>
        <TitleBar title="Jobs" />
        <Layout>
          <Layout.Section>
            <EmptyState
              heading="No jobs yet"
              image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png"
            >
              <p>Background jobs will appear here when you perform operations like syncing products.</p>
            </EmptyState>
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  return (
    <Frame>
      <Page>
        <TitleBar title="Jobs" />
        <Layout>
          {/* Filters Card */}
          <Layout.Section>
            <Card>
              <BlockStack gap="300">
                <Filters
                  onClearAll={() => {
                    setStatusFilter("");
                    setJobTypeFilter("");
                    setSearchParams(new URLSearchParams());
                  }}
                  filters={[
                    {
                      key: "status",
                      label: "Status",
                      filter: (
                        <ChoiceList
                          title="Status"
                          titleHidden
                          choices={[
                            { label: "All", value: "" },
                            { label: "Running", value: "running" },
                            { label: "Completed", value: "completed" },
                            { label: "Failed", value: "failed" },
                            { label: "Pending", value: "pending" },
                          ]}
                          selected={statusFilter ? [statusFilter] : [""]}
                          onChange={(value) => {
                            setStatusFilter(value[0] || "");
                            handleFilterChange("status", value[0] || "");
                          }}
                        />
                      ),
                    },
                    {
                      key: "jobType",
                      label: "Job Type",
                      filter: (
                        <ChoiceList
                          title="Job Type"
                          titleHidden
                          choices={[
                            { label: "All", value: "" },
                            { label: "Product Sync", value: "product_sync" },
                            { label: "Inventory Sync", value: "inventory_sync" },
                            { label: "Order Import", value: "order_import" },
                          ]}
                          selected={jobTypeFilter ? [jobTypeFilter] : [""]}
                          onChange={(value) => {
                            setJobTypeFilter(value[0] || "");
                            handleFilterChange("jobType", value[0] || "");
                          }}
                        />
                      ),
                    },
                  ]}
                />
              </BlockStack>
            </Card>
          </Layout.Section>

          {/* Jobs Table */}
          <Layout.Section>
            <Card padding="0">
              <IndexTable
                resourceName={resourceName}
                itemCount={data?.jobs?.length || 0}
                headings={[
                  { title: "Job Type" },
                  { title: "Status" },
                  { title: "Progress" },
                  { title: "Started" },
                  { title: "Duration" },
                ]}
              >
                {rowMarkup}
              </IndexTable>
            </Card>
          </Layout.Section>

          {/* Pagination */}
          <Layout.Section>
            <InlineStack align="center">
              <Pagination
                hasPrevious={!!data?.previous}
                hasNext={!!data?.next}
                onPrevious={handlePreviousPage}
                onNext={handleNextPage}
              />
            </InlineStack>
          </Layout.Section>
        </Layout>
      </Page>
    </Frame>
  );
}
