import { useState, useEffect } from 'react';
import SearchBar from '../components/SearchBar';
import CaseTable from '../components/CaseTable';
import Pagination from '../components/Pagination';

const PAGE_SIZE = 8;
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const Dashboard = () => {
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(0);
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState('');
    const [sortOrder, setSortOrder] = useState('asc');

    const fetchCases = async (query, page) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/api/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    page: page,
                    page_size: PAGE_SIZE,
                    sort_by: sortBy || undefined,
                    sort_order: sortOrder,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                if (response.status === 422 && data.detail && data.detail.length > 0) {
                    throw new Error(data.detail[0].msg);
                }
                throw new Error(data.detail || 'An error occurred while fetching data');
            }

            // Expected response shape from python backend:
            // { items: [...], total: X, page: Y, page_size: Z } or similar structure
            // Adjust according to the actual backend response format
            const resultsArray = data.data || data.items || data.results || (Array.isArray(data) ? data : []);
            setResults(resultsArray);

            // Calculate total pages if the backend provides a total count
            if (data.pagination && data.pagination.totalPages !== undefined) {
                setTotalPages(data.pagination.totalPages);
            } else if (data.total !== undefined) {
                setTotalPages(Math.ceil(data.total / PAGE_SIZE));
            } else if (data.total_pages !== undefined) {
                setTotalPages(data.total_pages);
            } else {
                // Fallback calculation for pagination if no total provided
                const count = resultsArray.length;
                setTotalPages(currentPage + (count === PAGE_SIZE ? 1 : 0));
            }
        } catch (err) {
            setError(err.message || 'Failed to connect to the server. Please try again later.');
            setResults([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCases(searchQuery, currentPage);
    }, [searchQuery, currentPage, sortBy, sortOrder]);

    const handleSearch = (query) => {
        setSearchQuery(query);
        setCurrentPage(1); // Reset to page 1 on new search
    };

    const handlePageChange = (newPage) => {
        setCurrentPage(newPage);
    };

    return (
        <div className="min-h-screen bg-gray-50 flex justify-center py-10 px-4 sm:px-6 lg:px-8">
            <div className="w-full max-w-6xl">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Case Monitoring</h1>
                    <p className="text-gray-500">Manage and monitor patient cases.</p>
                </div>

                <SearchBar onSearch={handleSearch} />

                <div className="flex justify-between items-center mb-4 px-2">
                    <div className="text-sm text-gray-500">
                        {loading ? 'Searching...' : (
                            totalPages > 0 ? `Showing page ${currentPage} of ${totalPages}` : ''
                        )}
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-gray-700">Sort by:</span>
                        <select
                            value={`${sortBy}-${sortOrder}`}
                            onChange={(e) => {
                                const [newSortBy, newSortOrder] = e.target.value.split('-');
                                setSortBy(newSortBy);
                                setSortOrder(newSortOrder);
                                setCurrentPage(1); // Reset to page 1 on sort change
                            }}
                            className="text-sm border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary px-3 py-1.5 cursor-pointer text-gray-700"
                        >
                            <option value="-asc">Most Relevant</option>
                            <option value="date-desc">Date (Newest First)</option>
                            <option value="date-asc">Date (Oldest First)</option>
                            <option value="age-desc">Age (Highest First)</option>
                            <option value="age-asc">Age (Lowest First)</option>
                            <option value="name-asc">Patient Name (A-Z)</option>
                            <option value="name-desc">Patient Name (Z-A)</option>
                            <option value="doctor-asc">Doctor Name (A-Z)</option>
                            <option value="doctor-desc">Doctor Name (Z-A)</option>
                        </select>
                    </div>
                </div>

                <CaseTable
                    data={results}
                    loading={loading}
                    error={error}
                />

                <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
                    disabled={loading}
                />
            </div>
        </div>
    );
};

export default Dashboard;
