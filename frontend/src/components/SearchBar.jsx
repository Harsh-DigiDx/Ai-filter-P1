import { useState } from 'react';

const SearchBar = ({ onSearch }) => {
    const [inputValue, setInputValue] = useState('');

    const handleSearch = () => {
        onSearch(inputValue);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    };

    return (
        <div className="flex w-full gap-3 mb-8">
            <div className="relative flex-1 flex items-center bg-[#f4f5f8] rounded-lg px-4 py-3.5 shadow-sm border border-transparent focus-within:border-gray-300 focus-within:bg-white transition-colors duration-200">
                <svg
                    className="w-6 h-6 text-slate-400 mr-3 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24" // fixed closing tag issue implicitly by replacing
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.75}
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                </svg>
                <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask me anything about patients... e.g., 'Show me all female patients' or 'Find patients admitted this week'"
                    className="w-full bg-transparent text-slate-700 placeholder-slate-400 focus:outline-none text-[15px]"
                />
            </div>
            <button
                onClick={handleSearch}
                className="px-8 py-3.5 bg-primary text-white rounded-lg hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 transition-colors font-medium cursor-pointer shadow-sm flex-shrink-0"
            >
                Search
            </button>
        </div>
    );
};

export default SearchBar;
