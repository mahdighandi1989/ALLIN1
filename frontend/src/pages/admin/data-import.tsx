import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  CloudUpload,
  PlayArrow,
  CheckCircle,
  Error as ErrorIcon,
  InsertDriveFile,
  Storage,
  Refresh,
  Assessment,
} from '@mui/icons-material';
import { api } from '@/utils/api';

interface FileInfo {
  name: string;
  size: number;
  modified: string;
}

interface ImportStats {
  customers: number;
  facilities: number;
  properties: number;
  guarantors: number;
  tasks: number;
  securities: number;
  journal: number;
  total: number;
  errors: string[];
}

interface ImportResponse {
  success: boolean;
  message: string;
  stats: ImportStats;
  files_processed: string[];
}

interface DbStats {
  customers: number;
  facilities: number;
  properties: number;
  guarantors: number;
  tasks: number;
  securities: number;
  journal: number;
  total: number;
}

export default function DataImportPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [dbStats, setDbStats] = useState<DbStats | null>(null);
  const [importResult, setImportResult] = useState<ImportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [filesRes, statsRes] = await Promise.all([
        api.get('/v1/data-import/files'),
        api.get('/v1/data-import/stats'),
      ]);
      setFiles(filesRes.data.files || []);
      setDbStats(statsRes.data);
    } catch (err: any) {
      if (err.response?.status === 401) {
        router.push('/login');
        return;
      }
      setError('Failed to load data: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const runImport = async () => {
    setImporting(true);
    setImportResult(null);
    setError(null);
    try {
      const res = await api.post('/v1/data-import/run');
      setImportResult(res.data);
      // Refresh stats after import
      const statsRes = await api.get('/v1/data-import/stats');
      setDbStats(statsRes.data);
      // Refresh files list
      const filesRes = await api.get('/v1/data-import/files');
      setFiles(filesRes.data.files || []);
    } catch (err: any) {
      if (err.response?.status === 401) {
        router.push('/login');
        return;
      }
      setError('Import failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setImporting(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleString('fa-IR');
  };

  return (
    <>
      <Head>
        <title>Data Import | Admin</title>
      </Head>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Typography variant="h4" component="h1">
            <Storage sx={{ mr: 1, verticalAlign: 'bottom' }} />
            Data Import
          </Typography>
          <Button
            startIcon={<Refresh />}
            onClick={fetchData}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Database Statistics */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Assessment sx={{ mr: 1, verticalAlign: 'bottom' }} />
              Database Statistics
            </Typography>
            {loading ? (
              <LinearProgress />
            ) : dbStats ? (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 2 }}>
                <Chip label={`Customers: ${dbStats.customers}`} color="primary" />
                <Chip label={`Facilities: ${dbStats.facilities}`} color="secondary" />
                <Chip label={`Properties: ${dbStats.properties}`} color="success" />
                <Chip label={`Guarantors: ${dbStats.guarantors}`} color="info" />
                <Chip label={`Tasks: ${dbStats.tasks}`} color="warning" />
                <Chip label={`Securities: ${dbStats.securities}`} color="error" />
                <Chip label={`Journal: ${dbStats.journal}`} color="default" />
                <Chip label={`Total: ${dbStats.total}`} variant="outlined" />
              </Box>
            ) : (
              <Typography color="text.secondary">No data</Typography>
            )}
          </CardContent>
        </Card>

        {/* Available Files */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <InsertDriveFile sx={{ mr: 1, verticalAlign: 'bottom' }} />
              Available Files for Import
            </Typography>
            {loading ? (
              <LinearProgress />
            ) : files.length > 0 ? (
              <TableContainer component={Paper} variant="outlined" sx={{ mt: 2 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>File Name</TableCell>
                      <TableCell align="right">Size</TableCell>
                      <TableCell align="right">Modified</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {files.map((file) => (
                      <TableRow key={file.name}>
                        <TableCell>{file.name}</TableCell>
                        <TableCell align="right">{formatFileSize(file.size)}</TableCell>
                        <TableCell align="right">{formatDate(file.modified)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Alert severity="info" sx={{ mt: 2 }}>
                No Excel files found in the data-import directory.
                <br />
                Please upload files to the <code>data-import/</code> folder in the repository.
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Import Action */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <CloudUpload sx={{ mr: 1, verticalAlign: 'bottom' }} />
              Run Import
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Click the button below to import data from all available Excel files into the database.
              This will create new records for customers, facilities, properties, guarantors, tasks, and securities.
            </Typography>
            <Button
              variant="contained"
              color="primary"
              size="large"
              startIcon={importing ? <CircularProgress size={20} color="inherit" /> : <PlayArrow />}
              onClick={runImport}
              disabled={importing || files.length === 0}
            >
              {importing ? 'Importing...' : 'Start Import'}
            </Button>
          </CardContent>
        </Card>

        {/* Import Result */}
        {importResult && (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {importResult.success ? (
                  <CheckCircle sx={{ mr: 1, verticalAlign: 'bottom', color: 'success.main' }} />
                ) : (
                  <ErrorIcon sx={{ mr: 1, verticalAlign: 'bottom', color: 'error.main' }} />
                )}
                Import Result
              </Typography>
              <Alert severity={importResult.success ? 'success' : 'error'} sx={{ mb: 2 }}>
                {importResult.message}
              </Alert>

              {importResult.files_processed.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Files Processed:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {importResult.files_processed.map((file) => (
                      <Chip key={file} label={file} size="small" variant="outlined" />
                    ))}
                  </Box>
                </Box>
              )}

              <Typography variant="subtitle2" gutterBottom>
                Records Imported:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
                <Chip label={`Customers: ${importResult.stats.customers}`} color="primary" size="small" />
                <Chip label={`Facilities: ${importResult.stats.facilities}`} color="secondary" size="small" />
                <Chip label={`Properties: ${importResult.stats.properties}`} color="success" size="small" />
                <Chip label={`Guarantors: ${importResult.stats.guarantors}`} color="info" size="small" />
                <Chip label={`Tasks: ${importResult.stats.tasks}`} color="warning" size="small" />
                <Chip label={`Securities: ${importResult.stats.securities}`} color="error" size="small" />
                <Chip label={`Journal: ${importResult.stats.journal}`} color="default" size="small" />
                <Chip label={`Total: ${importResult.stats.total}`} variant="outlined" size="small" />
              </Box>

              {importResult.stats.errors.length > 0 && (
                <>
                  <Typography variant="subtitle2" color="error" gutterBottom>
                    Errors:
                  </Typography>
                  <List dense>
                    {importResult.stats.errors.map((err, i) => (
                      <ListItem key={i}>
                        <ListItemIcon>
                          <ErrorIcon color="error" fontSize="small" />
                        </ListItemIcon>
                        <ListItemText primary={err} />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}
            </CardContent>
          </Card>
        )}
      </Container>
    </>
  );
}
