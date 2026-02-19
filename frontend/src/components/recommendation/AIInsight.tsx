import React from 'react';
import { Sparkles } from 'lucide-react';
import { Card, CardContent } from '../common/Card';

interface AIInsightProps {
  insight: string;
}

export function AIInsight({ insight }: AIInsightProps) {
  return (
    <Card className="bg-gradient-to-br from-primary-50 to-accent-50 dark:from-primary-900/20 dark:to-accent-900/20 border-primary-100 dark:border-primary-800">
      <CardContent>
        <div className="flex gap-3">
          <div className="w-8 h-8 bg-primary-100 dark:bg-primary-800 rounded-lg flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-4 h-4 text-primary-500" />
          </div>
          <div>
            <p className="text-sm font-medium text-primary-700 dark:text-primary-300 mb-1">
              AI Insight
            </p>
            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
              "{insight}"
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
