import React, { useState } from 'react';
import { Building2, Search } from 'lucide-react';
import { Card } from '../common/Card';
import { Input } from '../common/Input';
import { Bank } from '../../types';

interface BankSelectorProps {
  banks: Bank[];
  onSelect: (bank: Bank) => void;
}

const POPULAR_BANK_CODES = ['hdfc', 'icici', 'sbi', 'axis', 'kotak', 'yes'];

export function BankSelector({ banks, onSelect }: BankSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const popularBanks = banks.filter((b) =>
    POPULAR_BANK_CODES.includes(b.code.toLowerCase())
  );

  const filteredBanks = searchQuery
    ? banks.filter((b) =>
        b.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : banks;

  return (
    <div className="space-y-6">
      <Input
        placeholder="Search banks..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        leftIcon={<Search className="w-5 h-5" />}
        onClear={() => setSearchQuery('')}
      />

      {!searchQuery && popularBanks.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
            Popular Banks
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {popularBanks.map((bank) => (
              <BankCard key={bank.id} bank={bank} onClick={() => onSelect(bank)} />
            ))}
          </div>
        </div>
      )}

      <div>
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
          {searchQuery ? 'Search Results' : 'All Banks'}
        </h3>
        <div className="space-y-2">
          {filteredBanks.map((bank) => (
            <BankListItem key={bank.id} bank={bank} onClick={() => onSelect(bank)} />
          ))}
          {filteredBanks.length === 0 && (
            <p className="text-center text-gray-500 py-4">No banks found</p>
          )}
        </div>
      </div>
    </div>
  );
}

function BankCard({ bank, onClick }: { bank: Bank; onClick: () => void }) {
  return (
    <Card
      hoverable
      onClick={onClick}
      className="p-4 flex flex-col items-center justify-center text-center"
    >
      {bank.logo_url ? (
        <img src={bank.logo_url} alt={bank.name} className="w-10 h-10 mb-2" />
      ) : (
        <Building2 className="w-10 h-10 mb-2 text-gray-400" />
      )}
      <p className="font-medium text-sm">{bank.name}</p>
    </Card>
  );
}

function BankListItem({ bank, onClick }: { bank: Bank; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-left"
    >
      {bank.logo_url ? (
        <img src={bank.logo_url} alt={bank.name} className="w-8 h-8" />
      ) : (
        <Building2 className="w-8 h-8 text-gray-400" />
      )}
      <span className="font-medium">{bank.name}</span>
    </button>
  );
}
