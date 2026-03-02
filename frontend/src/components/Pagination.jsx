const Pagination = ({ currentPage, totalPages, onPageChange, disabled }) => {
    // Generate page numbers with ellipsis
    const getPageNumbers = () => {
        if (!totalPages || totalPages <= 0) return [];
        if (totalPages <= 5) {
            return Array.from({ length: totalPages }, (_, i) => i + 1);
        }

        if (currentPage <= 3) {
            return [1, 2, 3];
        }

        if (currentPage >= totalPages - 2) {
            return [1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
        }

        return [currentPage - 1, currentPage, currentPage + 1, '...', totalPages];
    };

    const pages = getPageNumbers();

    return (
        <div className="flex items-center justify-between mt-6 px-2">
            <div className="text-sm text-text-muted flex-shrink-0">
                Page {currentPage} of {totalPages || 1}
            </div>
            <div className="flex gap-2 w-full justify-end sm:w-auto">
                <button
                    onClick={() => onPageChange(currentPage - 1)}
                    disabled={disabled || currentPage === 1}
                    className="px-3 py-1.5 border border-border rounded-md text-sm font-medium text-text bg-card hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    Previous
                </button>

                <div className="flex gap-1 overflow-x-auto">
                    {pages.map((page, index) => (
                        page === '...' ? (
                            <span key={`ellipsis-${index}`} className="w-8 h-8 flex items-center justify-center text-text-muted">
                                ...
                            </span>
                        ) : (
                            <button
                                key={index}
                                onClick={() => onPageChange(page)}
                                disabled={disabled}
                                className={`w-8 h-8 rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary transition-colors flex items-center justify-center ${currentPage === page
                                    ? 'bg-primary text-white border-primary border'
                                    : 'border border-border text-text bg-card hover:bg-gray-50'
                                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                            >
                                {page}
                            </button>
                        )
                    ))}
                </div>

                <button
                    onClick={() => onPageChange(currentPage + 1)}
                    disabled={disabled || currentPage === totalPages || totalPages === 0}
                    className="px-3 py-1.5 border border-border rounded-md text-sm font-medium text-text bg-card hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    Next
                </button>
            </div>
        </div>
    );
};

export default Pagination;
