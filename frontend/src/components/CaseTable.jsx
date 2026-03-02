const CaseTable = ({ data, loading, error }) => {
    if (error) {
        return (
            <div className="w-full p-4 bg-red-50 border border-red-200 text-red-600 rounded-lg">
                {error}
            </div>
        );
    }

    return (
        <div className="w-full bg-card border border-border rounded-lg shadow-sm overflow-hidden relative min-h-[400px]">
            {loading && (
                <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-10 backdrop-blur-sm">
                    <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                </div>
            )}

            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-gray-50 border-b border-border">
                            <th className="p-4 font-semibold text-text-muted text-sm whitespace-nowrap">Doctor Name</th>
                            <th className="p-4 font-semibold text-text-muted text-sm whitespace-nowrap">Patient Name</th>
                            <th className="p-4 font-semibold text-text-muted text-sm whitespace-nowrap">Age</th>
                            <th className="p-4 font-semibold text-text-muted text-sm whitespace-nowrap">Gender</th>
                            <th className="p-4 font-semibold text-text-muted text-sm whitespace-nowrap">Date of Admission</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {(!data || data.length === 0) && !loading ? (
                            <tr>
                                <td colSpan="5" className="p-8 text-center text-text-muted">
                                    No cases found
                                </td>
                            </tr>
                        ) : (
                            data.map((row, idx) => (
                                <tr
                                    key={idx}
                                    className="hover:bg-gray-50 transition-colors group cursor-default"
                                >
                                    <td className="p-4 text-sm text-text font-medium">{row.Doctor || '-'}</td>
                                    <td className="p-4 text-sm text-text">{row.Name || '-'}</td>
                                    <td className="p-4 text-sm text-text-muted">{row.Age || '-'}</td>
                                    <td className="p-4 text-sm text-text-muted capitalize">{row.Gender || '-'}</td>
                                    <td className="p-4 text-sm text-text-muted">{row['Date of Admission'] || '-'}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default CaseTable;
